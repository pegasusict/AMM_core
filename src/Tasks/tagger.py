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

"""Writes tags of tracks to files.
It uses the mutagen library to write metadata to media files."""

from pathlib import Path

from task import Task
from enums import TaskType, Stage
from Singletons.config import Config
from Singletons.database import DB
from Singletons.logger import Logger
from dbmodels import DBFile, DBTrack, Track
from AudioUtils.tagger import Tagger as Tag
from AudioUtils.media_parser import get_file_type


class Tagger(Task):
    """This class is used to write tags to media files."""

    def __init__(self, config: Config, batch: list[str]) -> None:
        """
        Initializes the Tagger class.

        Args:
            config: The configuration object.
        """
        super().__init__(config=config, task_type=TaskType.TAGGER)
        self.config = config
        self.batch = batch  # type: ignore
        self.db = DB()
        self.logger = Logger(config)
        self.stage = Stage.TAGGED

    def run(self) -> None:
        """Runs the Tagger task."""
        session = self.db.get_session()
        for track_id in self.batch:  # type: ignore
            # Parse the media file
            file_path = "Unknown file"
            try:
                # get all tags for said track
                # Ensure track_id is an int
                if not isinstance(track_id, int):
                    track_id = int(str(track_id))
                session = self.db.get_session()
                db_track = session.get_one(DBTrack, DBTrack.id == track_id)
                track = Track()
                track.__dict__.update(db_track.__dict__)
                tags = track.get_tags()
                # get file associated with track
                file = track.files[0]
                file_id = file.id
                file_path = Path(file.file_path)
                if not file_path:
                    self.logger.error(f"Track {track_id} has no associated file.")
                    continue
                file_type = get_file_type(file_path)
                # write all tags to file
                tagger = Tag(file_path, str(file_type))
                tagger.set_tags(tags)
                self.update_file_stage(file_id, session)
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
                raise

            self.set_progress()
        session.commit()
        session.close()
