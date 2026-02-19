# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
#  This file is part of AMM (Audiophiles' Music Manager), GPLv3+.

"""
Modern Scanner Processor
------------------------

This processor periodically scans:

- Filesystem (import directory)
- Database (missing stages)
- Missing artwork (albums, persons, labels)

It emits batches for:
- Tasks (importer, parser, fingerprint, dedupe, etc.)
- ArtGetter
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from collections import defaultdict

from core.processor_base import ProcessorBase
from core.types import AsyncSessionLike, DBInterface
from core.registry import registry
from core.enums import StageType, TaskType, ArtType
# from core.exceptions import OperationFailedError

from config import Config
from Singletons import DBInstance, Logger
from core.dbmodels import DBFile, DBAlbum, DBPerson, DBLabel
from core.registry import registry

@registry.register_processor
class ScannerProcessor(ProcessorBase):
    """
    Modern Scanner Processor — Option B:
    - Broad StageType pipeline (IMPORT → ANALYSE → PROCESS → …)
    - Each StageType contains multiple TaskTypes (via registry)
    - Scanner runs missing tasks per file
    """

    name = "scanner"
    description = "Scans filesystem + DB for missing tasks per StageType"
    version = "3.1.0" # pyright: ignore[reportUnknownMemberType]

    depends = []
    heavy_io = True
    exclusive = True   # Only one scanner at a time

    # Deterministic stage order (bitwise enum values ascending)
    stage_order = [stage for stage in sorted(StageType, key=lambda stage: stage.value) if stage != StageType.NONE]

    
    def __init__(self, config: Config) -> None:
        super().__init__(config=config)
        self.config = config
        self.db: DBInterface = DBInstance # type: ignore
        self.logger = Logger()

        self.import_path = Path(config.get_path("import"))
        self.batch_size = config.get_int("scanner", "scanner_batch_size", 1000)

        # pulled from registry at runtime
        self.registry = registry


    # ---------------------------------------------------------
    # Main run loop
    # ---------------------------------------------------------
    async def run(self) -> None:
        async for session in self.db.get_session():

            # 1. Clean directories and detect new import files
            self._clean_empty_dirs()
            await self._detect_import_files()

            # 2. Stage + task scanning
            stage_batches = await self._scan_files(session)

            # Emit missing tasks
            for task_type, file_ids in stage_batches.items():
                for chunk in self._chunk(file_ids, self.batch_size):
                    self.emit_task(task_type=task_type, batch=chunk)

            # 3. Artwork scan
            artwork = self._scan_missing_art(session)
            if artwork:
                self.emit_task(TaskType.ART_GETTER, batch=artwork)

            await session.close()

        self.set_completed("Scanner cycle complete.")


    # ---------------------------------------------------------
    # Filesystem
    # ---------------------------------------------------------
    def _clean_empty_dirs(self) -> None:
        for directory in sorted(self.import_path.rglob("*"), key=lambda d: len(d.parts), reverse=True):
            if directory.is_dir():
                with contextlib.suppress(OSError):
                    directory.rmdir()
                    self.logger.debug(f"Removed empty directory: {directory}")

    async def _detect_import_files(self) -> None:
        if any(f.is_file() for f in self.import_path.rglob("*")):
            self.emit_task(task_type=TaskType.IMPORTER, batch=None)


    # ---------------------------------------------------------
    # DB Stage + Task scanning (Core of Option B)
    # ---------------------------------------------------------
    async def _scan_files(self, session: AsyncSessionLike) -> Dict[TaskType, List[int]]:
        """
        Determine missing tasks per StageType:
        - Look up next StageType in pipeline
        - Fetch task list from registry
        - Filter tasks already completed per file
        """
        stage_batches: Dict[TaskType, List[int]] = defaultdict(list)

        # Registry-driven mapping
        tasks_by_stage = self.registry._stage_records  # { StageType: [task_name, ...] }

        files = session.query(DBFile).all()
        for file in files:

            # DBFile already finished all stages?
            next_stage = self._next_stage(file.stage_type)
            if not next_stage:
                continue

            # Get all tasks declared for that stage
            task_names = tasks_by_stage.get(next_stage, [])

            # Determine which tasks still need to run
            for tname in task_names:
                if tname not in file.completed_tasks:
                    ttype = self.registry.get_task_class(tname).task_type
                    stage_batches[ttype].append(file.id)

        return stage_batches


    def _next_stage(self, current: StageType) -> Optional[StageType]:
        """
        Return the next StageType after the file’s current stage.
        """
        try:
            i = self.stage_order.index(current)
            return self.stage_order[i + 1]
        except (ValueError, IndexError):
            return None


    # ---------------------------------------------------------
    # Artwork scanning
    # ---------------------------------------------------------
    def _scan_missing_art(self, session: AsyncSessionLike) -> Dict[str, ArtType]:
        missing: Dict[str, ArtType] = {}

        # Albums
        for album in session.query(DBAlbum).filter(DBAlbum.picture.is_(None)).all():
            if album.mbid:
                missing[album.mbid] = ArtType.ALBUM

        # Persons
        for person in session.query(DBPerson).filter(DBPerson.picture.is_(None)).all():
            if person.mbid:
                missing[person.mbid] = ArtType.ARTIST

        # Labels
        for label in session.query(DBLabel).filter(DBLabel.picture.is_(None)).all():
            if label.mbid:
                missing[label.mbid] = ArtType.LABEL

        return missing


    # ---------------------------------------------------------
    @staticmethod
    def _chunk(items: List[int], size: int) -> Iterable[List[int]]:
        for i in range(0, len(items), size):
            yield items[i:i + size]
