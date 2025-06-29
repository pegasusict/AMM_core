# -*- coding: utf-8 -*-
#  Copyleft 2021-2025 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  AMM is free software: you can redistribute it and/or modify  it under the terms of the
#   GNU General Public License as published by  the Free Software Foundation, either version 3
#   of the License or any later version.
#
#  AMM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with AMM.  If not, see <https://www.gnu.org/licenses/>.

"""
Scans filesystem and database for things to be processed by other tasks.
"""

import contextlib
from pathlib import Path
from typing import Optional
from collections import defaultdict

from . import TaskManager, Task, Importer, ArtGetter
from ..enums import Stage, TaskType, ArtType
from ..dbmodels import DBFile, DBAlbum, DBPerson, DBLabel
from ..Singletons import Config, DBInstance, Logger


class Scanner(Task):
    """
    Scans filesystem and database for things to be processed by other tasks.
    """

    stage_to_tasktype: dict[Stage, TaskType] = {
        Stage.IMPORTED: TaskType.IMPORTER,
        Stage.PARSED: TaskType.PARSER,
        Stage.FINGERPRINTED: TaskType.FINGERPRINTER,
        Stage.DEDUPED: TaskType.DEDUPER,
        Stage.TRIMMED: TaskType.TRIMMER,
        Stage.NORMALIZED: TaskType.NORMALIZER,
        Stage.ART_RETRIEVED: TaskType.ART_GETTER,
        Stage.LYRICS_RETRIEVED: TaskType.LYRICS_GETTER,
        Stage.CONVERTED: TaskType.CONVERTER,
        Stage.TAGGED: TaskType.TAGGER,
        Stage.SORTED: TaskType.SORTER,
    }

    def __init__(self, config: Config, batch=None, kwargs=None):
        super().__init__(config=config, task_type=TaskType.SCANNER)
        self.config = config
        self.db = DBInstance
        self.logger = Logger(config)
        self.is_idle_task = True
        self.import_path = Path(self.config.get_path("import"))
        # Dynamically include all defined Stage flags except NONE
        self.required_stages = Stage(0)
        for stage in Stage:
            if stage != Stage.NONE:
                self.required_stages |= stage
        self.task_manager = TaskManager()
        self.batch_size = self.config.get_int("scanner", "scanner_batch_size", 1000)  # default 1000

    async def run(self) -> None:
        """
        Runs the Scanner Task.
        """
        async for session in self.db.get_session():
            # Remove empty directories from the import folder
            self.remove_empty_dirs(self.import_path)

            # Check for new files to import
            await self.check_new_import_files()

            # Assess stages and reschedule processing tasks
            await self.scan_and_reschedule(session)

            if art_batch := self.collect_missing_artwork(session):
                self.logger.debug(f"Scanner: Launching ART_GETTER with batch: {art_batch}")
                await self.task_manager.start_task(ArtGetter, art_batch)
            else:
                self.logger.debug("Scanner: No missing artwork detected.")

            await session.close()
        self.task_manager._idle_task_running = False

    def remove_empty_dirs(self, path: Path):
        for directory in sorted(path.rglob("*"), key=lambda d: len(d.parts), reverse=True):
            if directory.is_dir():
                with contextlib.suppress(OSError):
                    directory.rmdir()
                    self.logger.debug(f"Removed empty directory: {directory}")

    async def check_new_import_files(self):
        new_files = [file for file in self.import_path.rglob("*") if file.is_file()]
        self.logger.info(f"Scanner: Found {len(new_files)} files in import folder.")
        if new_files:
            tm = TaskManager()
            await tm.start_task(Importer, None)

    async def scan_and_reschedule(self, session):
        files = session.query(DBFile).all()
        batch_tasks: dict[TaskType, list[int]] = defaultdict(list)

        for file in files:
            if next_stage := self.get_next_missing_stage(file.stage):
                if task_type := self.stage_to_tasktype.get(next_stage):
                    batch_tasks[task_type].append(file.id)
                    self.logger.debug(f"Scanner: File {file.id} added to {task_type.name} batch.")
                else:
                    self.logger.debug(f"Scanner: No task mapped for Stage {next_stage.name}")
            else:
                self.logger.debug(f"Scanner: File {file.id} has all required stages.")

        # Launch batch tasks
        for task_type, file_ids in batch_tasks.items():
            task_class = self.task_manager._get_task_class(task_type)
            for i in range(0, len(file_ids), self.batch_size):  # type: ignore
                batch = file_ids[i : i + self.batch_size]  # type: ignore
                self.logger.debug(f"Scanner: Launching {task_type.name} task for batch: {batch}")
                await self.task_manager.start_task(
                    task_class=task_class,
                    batch=batch,
                )

    def collect_missing_artwork(self, session) -> dict[str, ArtType]:
        """Returns a dict of mbid -> ArtType for missing Album, Person, Label artwork."""
        result = {}

        # Albums missing artwork
        albums = session.query(DBAlbum).filter(DBAlbum.picture.is_(None)).all()  # type: ignore
        for album in albums:
            if album.mbid:
                result[album.mbid] = ArtType.ALBUM
                self.logger.debug(f"Scanner: Album {album.id} missing picture.")

        # Persons missing artwork
        persons = session.query(DBPerson).filter(DBPerson.picture.is_(None)).all()  # type: ignore
        for person in persons:
            if person.mbid:
                result[person.mbid] = ArtType.ARTIST
                self.logger.debug(f"Scanner: Person {person.id} missing picture.")

        # Labels missing artwork
        labels = session.query(DBLabel).filter(DBLabel.picture.is_(None)).all()  # type: ignore
        for label in labels:
            if label.mbid:
                result[label.mbid] = ArtType.LABEL
                self.logger.debug(f"Scanner: Label {label.id} missing picture.")

        return result

    def get_missing_stages(self, file_stage: int) -> list[Stage]:
        file_stage = Stage(file_stage)
        return [stage for stage in Stage if stage in self.required_stages and not (file_stage & stage)]

    def get_next_missing_stage(self, file_stage: int) -> Optional[Stage]:
        missing = self.get_missing_stages(file_stage)
        return min(missing, key=lambda stage: stage.value) if missing else None
