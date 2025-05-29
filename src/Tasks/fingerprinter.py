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

from ..models import Stages
from task import Task, TaskType
from Singletons.config import Config
from Singletons.database import DB
from Singletons.logger import Logger
from AudioUtils.acoustid import AcoustID


class FingerPrinter(Task):
    """This Task is aimed at fingerprinting the audio of the file
    in order to identify it with the aid of MusicBrainz."""

    batch: dict[int, str | Path]

    def __init__(self, config: Config, batch: dict[int, str | Path]):
        """
        Initializes the Parser class.

        Args:
            config: The configuration object.
            batch:  A dictionairy containing file_id's and filepaths
        """

        super().__init__(config, task_type=TaskType.FINGERPRINTER)
        self.config = config
        self.batch = batch  # type: ignore
        self.db = DB()
        self.logger = Logger(config)

    def run(self) -> None:
        """
        Runs the parser task.
        It parses the media files in the import path and extracts metadata from them.
        """
        for file_id, file_path in self.batch:  # type: ignore
            try:
                path = Path(str(file_path))
                acoustid = AcoustID(path)
                metadata = acoustid.process()
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
                continue

            # Add the metadata to the database
            self.db.update_file(str(file_path), metadata)
            self.db.set_file_stage(file_id, Stages.FINGERPRINTED)
            self.set_progress()
