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

"""This module eliminates duplicate files, taking into account audio quality (bitrate, codec)."""

from pathlib import Path
from ..dbmodels import DBFile, Track
from ..Singletons.logger import Logger
from ..Enums import CodecPriority, TaskType
from ..Singletons.config import Config
from ..Singletons.database import DB
from .task import Task


class Deduper(Task):
    """This class is used to eliminate duplicate files based on audio quality."""

    batch: list[int]  # type: ignore

    def __init__(self, config: Config, batch: list[int]):
        """
        Initializes the Deduper class.

        Args:
            config: The configuration object.
            batch: List of track ids to process for deduplication.
        """
        super().__init__(config=config, task_type=TaskType.DEDUPER)
        self.config = config
        self.logger = Logger(config)
        self.db = DB()
        self.batch = batch  # type: ignore

    def run(self):
        """Runs The Deduper Task."""
        for track_id in self.batch:
            track = Track(track_id)
            if len(track.files) > 1:
                # Sort files by bitrate and codec
                track.files.sort(key=lambda f: (CodecPriority[f.codec], f.bitrate), reverse=True)
                # Keep the highest quality file
                # best_file = track.files[0]
                # Remove lower quality files
                for file in track.files[1:]:
                    path = Path(file.path)
                    self.logger.info(f"Removing duplicate file: {path}")
                    path.unlink()
                    session = self.db.get_session()

                    # Remove the file from the database
                    dbfile = session.get(DBFile, DBFile.id == file.id)
                    session.delete(dbfile)
                    session.commit()
                    self.logger.info(f"Removed {file.id} from database")
                    session.close()
            else:
                self.logger.info(f"Track {track_id} has no duplicates to remove")
            self.set_progress()
        self.logger.info("Deduplication complete")
