# -*- coding: utf-8 -*-
#  Copyleft 2021-2025 Mattijs Snepvangers.
#  This file is part of AMM, released under GPLv3+.

"""Lyrics Getter Task."""

from ..Singletons import Config, DBInstance, Logger
from ..core.task_base import TaskBase
from ..dbmodels import DBTrack, DBTrackLyric
from ..exceptions import DatabaseError
from ..enums import StageType


class LyricsGetter(TaskBase):
    """
    New-style LyricsGetter Task.

    - Uses Singletons: Config, DBInstance, Logger
    - Fetches lyrics using the new unified LyricsGetter util
      (injected via depends = ["lyricsgetter"])
    - Async DB operations
    - Updates file stage
    """

    # registry tells the loader which utils this task requires
    depends = ["lyricsgetter"]

    def __init__(self, batch: list[int], *, lyricsgetter):
        """
        Args:
            batch: list of track IDs that should be processed.
            lyricsgetter: injected util from registry
        """
        super().__init__()
        self.config = Config
        self.db = DBInstance
        self.logger = Logger(self.config)

        self.batch = batch
        self.lyricsgetter = lyricsgetter
        self.stage_type:StageType = StageType.LYRICS_RETRIEVED



    async def run(self) -> None:
        """
        Fetch lyrics for all tracks in the batch and store them in DB.
        """
        async for session in self.db.get_session():
            try:
                for track_id in self.batch:

                    # Load track
                    track = session.get_one(DBTrack, DBTrack.id == int(track_id))
                    if track is None:
                        raise DatabaseError(f"Invalid track id: {track_id}")

                    # Resolve metadata
                    title = track.title
                    artist = track.performers[0].full_name if track.performers else None

                    if not artist or not title:
                        self.logger.warning(
                            "LyricsGetter: Track %s missing artist/title", track_id
                        )
                        continue

                    # Prepare query string
                    query = f"{artist} - {title}"

                    # Fetch lyrics using new unified util
                    lyrics = await self.lyricsgetter.get_lyrics(query)

                    # Store in DB if found
                    if lyrics:
                        obj = DBTrackLyric(Lyric=lyrics, track=track)
                        session.add(obj)

                        # Update stage for all associated files
                        for f in track.files:
                            self.update_file_stage(f.id, session)

                        self.set_progress()
                    else:
                        self.logger.info(
                            "LyricsGetter: No lyrics found for '%s'", query
                        )

                await session.commit()

            except Exception as e:
                self.logger.exception(
                    "LyricsGetter: Error while processing batch: %s", e
                )

            finally:
                await session.close()
