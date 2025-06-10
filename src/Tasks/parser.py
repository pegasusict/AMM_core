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
    This class is used to parse media files and extract metadata from them.
    """

    def __init__(self, config: Config, batch: list[Path]):
        """
        Initializes the Parser class.

        Args:
            config: The configuration object.
        """
        super().__init__(config=config, task_type=TaskType.PARSER)
        self.config = config
        self.batch = batch  # type: ignore
        self.db = DB()
        self.logger = Logger(config)
        self.parser = MediaParser(config)

    def run(self) -> None:
        """
        Runs the parser task.
        """
        for file in self.batch:  # type: ignore
            # Parse the media file
            try:
                metadata = self.parser.parse(Path(str(file)))
                file = self.db.register_file(str(file), metadata).first()  # type: ignore
                if file_id := file.get("file_id", None) is not None:  # type: ignore
                    self.db.set_file_stage(file_id, Stage.IMPORTED)
                else:
                    raise DatabaseError("An error occured saving the file to the Database.")
            except Exception as e:
                self.logger.error(f"Error processing file {file}: {e}")
                continue

            self.set_progress()
