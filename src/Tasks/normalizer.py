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

"""Normalizer Task."""

from pathlib import Path

from ..enums import Stage, TaskType
from . import Task
from ..Singletons import Config, DBInstance, Logger
from ..AudioUtils.normalizer import normalize
from ..AudioUtils.media_parser import get_file_type


class Normalizer(Task):
    """This Task is aimed at normalizing the audio of the file."""

    batch: dict[int, str | Path]

    def __init__(self, config: Config, batch: dict[int, Path]):
        """
        Initializes the Normalizer class.

        Args:
            config: The configuration object.
        """
        super().__init__(config=config, task_type=TaskType.NORMALIZER)
        self.config = config
        self.batch = batch  # type: ignore
        self.db = DBInstance
        self.logger = Logger(config)
        self.stage = Stage.NORMALIZED

    async def run(self) -> None:
        """
        Runs the task.
        """
        async for session in self.db.get_session():
            for file_id, path in self.batch:  # type: ignore
                try:
                    file_type = get_file_type(Path(path))
                    normalize(file=Path(path), file_type=str(file_type))
                    self.update_file_stage(file_id, session)
                except Exception as e:
                    self.logger.error(f"Error processing file {path}: {e}")
                    continue

                self.set_progress()
            await session.commit()
            await session.close()
