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

"""Parses media files and extracts metadata from them.
It uses the mutagen library to read and write metadata to media files.
"""

from pathlib import Path

from ..Exceptions import DatabaseError
from ..models import Stage
from .task import Task, TaskType
from ..Singletons.config import Config
from ..Singletons.database import DB
from ..Singletons.logger import Logger
from ..AudioUtils.media_parser import MediaParser


class Parser(Task):
    """
    Parses media files in a batch, extracts metadata, and registers them in the database.
    """

    def __init__(self, config: Config, batch: list[Path]):
        super().__init__(config=config, task_type=TaskType.PARSER)
        self.config = config
        self.batch = batch
        self.db = DB()
        self.logger = Logger(config)
        self.parser = MediaParser(config)

    def run(self) -> None:
        """
        Parses all files in the batch, extracts metadata, and registers them in the database.
        Skips files that are already imported.
        """
        for file_path in self.batch:  # type: ignore
            try:
                if self.db.file_exists(str(file_path)):
                    self.logger.info(f"Skipping already imported file: {file_path}")
                    continue

                metadata = self.parser.parse(file_path)  # type: ignore
                db_file = self.db.register_file(str(file_path), metadata).first()  # type: ignore

                if db_file is None:
                    raise DatabaseError("DB did not return a valid file object.")

                file_id = db_file.get("file_id")
                if file_id is not None:
                    self.db.set_file_stage(file_id, Stage.IMPORTED)
                else:
                    raise DatabaseError("Missing file_id after saving to the database.")

            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
                continue

            self.set_progress()
