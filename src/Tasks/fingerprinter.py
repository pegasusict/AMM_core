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

"""Fingerprinter Task."""

from pathlib import Path

from ..models import DBFile, Stage
from task import Task, TaskType
from Singletons.config import Config
from Singletons.database import DB
from Singletons.logger import Logger
from AudioUtils.acoustid import AcoustID

# Imports for required protocol implementations
from AudioUtils.utils.acoustidhttpclient import AcoustIDHttpClient
from AudioUtils.utils.durationparser import DurationParser
from AudioUtils.utils.simpletagger import SimpleTagger


class FingerPrinter(Task):
    """Task that fingerprints and identifies audio files via AcoustID."""

    batch: list[int]

    def __init__(self, config: Config, batch: list[int]):
        super().__init__(config=config, task_type=TaskType.FINGERPRINTER)
        self.config = config
        self.batch = batch  # type: ignore
        self.db = DB()
        self.logger = Logger(config)

    async def run(self) -> None:
        """Runs the fingerprinting task asynchronously."""
        for file_id in self.batch:
            try:
                session = self.db.get_session()
                file = session.get_one(DBFile, id == file_id)
                file_path = Path(file.path)
                if not file_path.exists():
                    self.logger.error(f"File {file_path} does not exist.")
                    continue
                metadata = await self.process_file(file_path)
            except Exception as e:
                self.logger.error(f"Error processing file {file_id}: {e}")
                continue

            self.db.update_file(str(file_path), metadata)  # type: ignore
            self.db.set_file_stage(file_id, Stage.FINGERPRINTED)
            self.set_progress()

    async def process_file(self, path: Path) -> dict[str, str | None]:
        """Fingerprints and looks up metadata for a single file."""
        acoustid = AcoustID(path=path, acoustid_client=AcoustIDHttpClient(), tagger=SimpleTagger(path), parser=DurationParser(), logger=self.logger)
        return await acoustid.process()
