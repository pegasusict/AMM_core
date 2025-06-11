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

"""Trimmer task for removing silences from audio files."""

from pathlib import Path
from typing import Sequence

from task import Task, TaskType
from Singletons.config import Config
from Singletons.logger import Logger
from AudioUtils.trimmer import SilenceTrimmer
from dbmodels import Codec
from Exceptions import FileError


class Trimmer(Task):
    """Trims silences from the start and end of songs."""

    def __init__(self, batch: Sequence[Path], config: Config = Config()) -> None:
        """
        Initializes the Trimmer task.

        Args:
            batch: A sequence of file paths to trim.
            config: Configuration object.
        """
        super().__init__(config=config, task_type=TaskType.TRIMMER)
        self.batch = batch  # type: ignore
        self.logger = Logger(config)

    def run(self) -> None:
        """Runs the trimmer on all files in the batch."""
        for path in self.batch:  # type: ignore
            self._trim_file(path)  # type: ignore
            self.set_progress()

    def _trim_file(self, path: Path) -> None:
        """Trims silence from a single file."""
        try:
            extension = path.suffix.lower().lstrip(".")
            if not extension:
                raise FileError("Unknown or missing file extension.")

            codec = Codec.__members__.get(extension.upper())
            if not codec:
                raise FileError(f"Unsupported codec: {extension}")

            trimmer = SilenceTrimmer(path, codec)
            trimmer.trim_silences()  # Ensure it's called
            self.logger.info(f"Trimmed silences from: {path}")

        except Exception as e:
            self.logger.error(f"Error trimming file {path}: {e}")
