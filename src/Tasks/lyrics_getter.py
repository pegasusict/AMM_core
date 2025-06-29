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
from .task import Task
from ..Singletons import Config, DBInstance, Logger
from ..AudioUtils.lyrics_getter import LyricsGetter as Lyrics
from ..dbmodels import DBTrackLyric, DBTrack
from ..enums import Stage, TaskType


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
        self.db = DBInstance
        self.logger = Logger(config)
        self.lyrics_getter = Lyrics()
        self.stage = Stage.LYRICS_RETRIEVED

    async def run(self) -> None:
        """
        Runs the parser task.
        It parses the media files in the import path and extracts metadata from them.
        """
        try:
            async for session in self.db.get_session():
                for track_id in self.batch:
                    track = DBTrack(id=int(track_id))
                    track_title = track.title
                    track_artist = track.performers[0].full_name
                    lyrics_getter = Lyrics()
                    lyric = lyrics_getter.get_lyrics(
                        artist=track_artist, title=track_title
                    )

                    track = session.get_one(DBTrack, DBTrack.id == int(track_id))
                    if track is None:
                        raise DatabaseError(f"Incorrect track id: {track_id}")
                    obj = DBTrackLyric(Lyric=lyric, track=track)  # type: ignore
                    session.add(obj)

                    for file in track.files:  # type: ignore
                        self.update_file_stage(file.id, session)
                    self.set_progress()
                await session.commit()
                await session.close()
        except Exception as e:
            self.logger.error(f"Error processing track {track_id}: {e}")  # type: ignore
