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

from sqlmodel import select

from task import Task, TaskType
from Singletons.config import Config
from Singletons.database import DB
from Singletons.logger import Logger
from models import DBTrack, Track
from AudioUtils.tagger import Tagger as Tag
from AudioUtils.media_parser import get_file_type


class Tagger(Task):
    """This class is used to write tags to media files."""

    def __init__(self, config:Config, batch:list[Path]):
        """
        Initializes the Parser class.

        Args:
            config: The configuration object.
        """
        super().__init__(config, task_type=TaskType.PARSER)
        self.config = config
        self.batch = batch
        self.db = DB()
        self.logger = Logger(config)

    def run(self) -> None:
        """
        Runs the Tagger task.
        """
        for track_id in self.batch:
            # Parse the media file
            file="Unknown file"
            try:
                # get all tags for said track
                # Ensure track_id is an int
                if isinstance(track_id, int):
                    statement = select(DBTrack).where(DBTrack.id == track_id)
                else:
                    statement = select(DBTrack).where(DBTrack.id == int(str(track_id)))
                session = self.db.get_session()
                db_track = session.exec(statement).first()
                track = Track()
                track.__dict__.update(db_track.__dict__)
                tags = track.get_tags()
                # get file associated with track
                file = track.file
                file_type = get_file_type(Path(file))
                # write all tags to file
                tagger = Tag(Path(file), str(file_type))
                tagger.set_tags(tags)
            except Exception as e:
                self.logger.error(f"Error processing file {file}: {e}")
                raise

            self.set_progress()
