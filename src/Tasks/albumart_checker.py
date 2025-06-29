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

"""Checks the database for tracks that have albumart for
their primary albums and sets the appropriate stage flag for
the files belonging to the track.
"""

from pathlib import Path
from typing import Any

from sqlalchemy.orm.strategy_options import selectinload
from sqlmodel import select

from ..enums import Stage, TaskType
from ..dbmodels import DBFile, DBTrack, DBAlbum, DBAlbumTrack, DBPicture
from .task import Task
from ..Singletons import Config, DBInstance, Logger


class AlbumArt_Checker(Task):
    """
    Checks the database for tracks that have albumart for
    their primary albums and sets the appropriate stage flag for
    the files belonging to the track.
    """

    def __init__(self, config: Config, batch: dict[int, Path]):
        super().__init__(config=config, task_type=TaskType.ART_CHECKER)
        self.config = config
        self.db = DBInstance
        self.logger = Logger(config)
        self.stage = Stage.ART_RETRIEVED
        self.batch: list[dict[str, Any]]

    async def run(self) -> None:
        """
        Runs the ArtChacker Task.
        """
        async for session in DBInstance.get_session():
            self.batch = session.exec(  # type: ignore
                select(DBFile)
                .join(DBTrack, DBFile.track_id == DBTrack.id)  # type: ignore
                .join(DBAlbumTrack, DBAlbumTrack.track_id == DBTrack.id)  # type: ignore
                .join(DBAlbum, DBAlbumTrack.album_id == DBAlbum.id)  # type: ignore
                .join(DBPicture, DBAlbum.id == DBPicture.album_id)  # type: ignore
                .options(
                    selectinload(DBFile.track),  # type: ignore
                    selectinload(DBFile.track).selectinload(DBTrack.album_tracks),  # type: ignore
                )
            ).all()  # type: ignore
            for file in self.batch:  # type: ignore
                self.update_file_stage(file.id, session)  # type: ignore
                self.set_progress()
            await session.commit()
            await session.close()
