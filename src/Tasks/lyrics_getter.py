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

from task import Task, TaskType
from Singletons.config import Config
from Singletons.database import DB
from Singletons.logger import Logger
from AudioUtils.lyrics_getter import get_lyrics
from models import DBTrackLyric, DBTrack

class LyricsGetter(Task):
    """This Task is aimed at getting the lyrics
    corresponding with the current Track."""
    batch:dict[str,str]

    def __init__(self, config:Config, batch:dict[str, str]):
        """
        Initializes the LyricsGetter class.

        Args:
            config: The configuration object.
            batch: A dictionary mapping track ids to track mbids
        """
        super().__init__(config, task_type=TaskType.LYRICS_GETTER)
        self.config = config
        self.batch = batch # type: ignore
        self.db = DB()
        self.logger = Logger(config)

    def run(self) -> None:
        """
        Runs the parser task.
        It parses the media files in the import path and extracts metadata from them.
        """
        try:
            for track_id, mbid in self.batch.items():
                track = DBTrack(id=int(track_id))
                track_title = track.titles[0].title
                track_artist = track.performers[0].names[0].name
                lyrics = get_lyrics(artist=track_artist, title=track_title)
                track = DBTrack(id=int(track_id))
                object = DBTrackLyric(id=0, Lyric=lyrics, track=track)
                session = DB().get_session()
                session.add(object)
                session.commit()
        except Exception as e:
            self.logger.error(f"Error processing track {mbid}: {e}") # type: ignore

        self.set_progress()
