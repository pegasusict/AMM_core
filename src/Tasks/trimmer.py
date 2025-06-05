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

"""Trims silences of start and end of songs."""

from pathlib import Path

from task import Task, TaskType
from Singletons.config import Config
from Singletons.database import DB
from Singletons.logger import Logger
from AudioUtils.trimmer import SilenceTrimmer
from models import Codec
from Exceptions import FileError


class Trimmer(Task):
    """Trims silences of start and end of songs."""

    batch: list[Path]

    def __init__(self, batch: list[Path], config: Config = Config()):
        """
        Initializes the Trimmer class.

        Args:
            config: The configuration object.
            batch: An iterable of files to process.
        """
        super().__init__(config, task_type=TaskType.PARSER)
        self.config = config
        self.batch = batch  # type: ignore
        self.db = DB()
        self.logger = Logger(config)

    def run(self) -> None:
        """
        Runs the Tagger task.
        """
        for path in self.batch:
            try:
                extension = Path(path).suffix.lower().lstrip(".")
                if extension is None:
                    raise FileError("Unknown or no extension found")
                codec = Codec[extension]
                trimmer = SilenceTrimmer(path, codec)
                trimmer.trim_silences
            except Exception as e:
                self.logger.error(f"Error processing file {path}: {e}")
                raise

            self.set_progress()
