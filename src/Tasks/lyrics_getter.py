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

"""Lyrics Getter Task."""

from ..exceptions import DatabaseError
from task import Task, TaskType
from Singletons.config import Config
from Singletons.database import DB
from Singletons.logger import Logger
from AudioUtils.lyrics_getter import LyricsGetter as Lyrics
from dbmodels import DBTrackLyric, DBTrack, DBFile
from ..enums import Stage


class LyricsGetter(Task):
    """This Task is aimed at getting the lyrics
    corresponding with the current Track."""

    batch: list[int]

    def __init__(self, config: Config, batch: list[int]) -> None:
        """
        Initializes the LyricsGetter class.

        Args:
            config: The configuration object.
            batch: A dictionary mapping track ids to track mbids
        """
        super().__init__(config=config, task_type=TaskType.LYRICS_GETTER)
        self.config = config
        self.batch = batch  # type: ignore
        self.db = DB()
        self.logger = Logger(config)
        self.lyrics_getter = Lyrics()

    def run(self) -> None:
        """
        Runs the parser task.
        It parses the media files in the import path and extracts metadata from them.
        """
        try:
            session = self.db.get_session()
            for track_id in self.batch:
                track = DBTrack(id=int(track_id))
                track_title = track.title
                track_artist = track.performers[0].full_name
                lyrics = Lyrics.get_lyrics(artist=track_artist, title=track_title)  # type: ignore

                track = session.get_one(DBTrack, DBTrack.id == int(track_id))
                if track is None:
                    raise DatabaseError(f"Incorrect track id: {track_id}")
                obj = DBTrackLyric(Lyric=lyrics, track=track)  # type: ignore
                session.add(obj)

                for file_id in track.files:  # type: ignore
                    dbfile = session.get_one(DBFile, DBFile.id == file_id)
                    dbfile.stage = int(Stage(dbfile.stage) | Stage.LYRICS_RETRIEVED)
                    session.add(dbfile)
                self.set_progress()
            session.commit()
            session.close()
        except Exception as e:
            self.logger.error(f"Error processing track {track_id}: {e}")  # type: ignore
