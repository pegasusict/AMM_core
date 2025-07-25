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

"""This module finds duplicate files based on the information of the database."""

from sqlmodel import select

from .taskmanager import TaskManager

from . import Task, Deduper
from ..exceptions import DatabaseError
from ..enums import TaskType
from ..Singletons import Logger, Config, DBInstance
from ..dbmodels import DBTrack, DBFile


class DuplicateChecker(Task):
    """This class is used to check for duplicate files in the database."""

    def __init__(self, config: Config):
        """
        Initializes the DuplicateChecker class.

        Args:
            config: The configuration object.
        """
        super().__init__(config=config, task_type=TaskType.DUPLICATE_CHECKER)
        self.config = config
        self.logger = Logger(config)
        self.db = DBInstance

    async def run(self):
        """Runs The DuplicateChecker Task."""
        async for session in self.db.get_session():
            try:
                stmt = (
                    select(DBTrack)
                    .join(DBFile)
                    .group_by(DBTrack.id)  # type: ignore
                    .having(func.count(DBFile.id) > 1)  # type: ignore  # noqa: F821
                )

                duplicates = session.exec(stmt)
            except Exception as e:
                self.logger.error(f"Error while checking for duplicates: {e}")
                raise DatabaseError(f"Database error: {e}") from e
            if not duplicates:
                self.logger.info("No duplicate files found.")
                return
            self.logger.info(f"Found {len(duplicates)} duplicate files.")  # type: ignore
            # Create a task to eliminate all duplicates
            task = Deduper(config=self.config, batch=[track.id for track in duplicates])  # type: ignore
            tm = TaskManager()
            tm.register_task(task)
