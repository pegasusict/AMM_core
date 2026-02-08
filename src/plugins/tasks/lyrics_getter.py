# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
#  Part of AMM, GPLv3+

"""Lyrics Getter Task — new unified plugin architecture."""

from __future__ import annotations

from typing import ClassVar, List

from config import Config
from Singletons import DBInstance, Logger
from core.task_base import TaskBase, register_task
from core.types import DBInterface, LyricsGetterProtocol
from core.enums import TaskType, StageType
from dbmodels import DBTrack, DBTrackLyric
from core.exceptions import DatabaseError


@register_task
class LyricsGetter(TaskBase):
    """
    Retrieve lyrics for tracks using the new lyricsgetter audio util.
    """

    name = "lyrics_getter"
    description = "Fetches lyrics online and stores them in the database."
    version = "2.0.0"
    author = "Mattijs Snepvangers"

    task_type = TaskType.LYRICS_GETTER
    stage_type = StageType.METADATA
    stage_name = "metadata"

    depends = ["lyricsgetter"]

    # required new flags
    exclusive: ClassVar[bool] = False           # can run concurrently
    heavy_io: ClassVar[bool] = True             # network + DB operations

    def __init__(
        self,
        lyricsgetter: LyricsGetterProtocol,
        *,
        batch: List[int]
    ) -> None:
        # No super() call — TaskBase handles base initialization automatically
        self.logger = Logger()
        self.config = Config.get_sync()
        self.db: DBInterface = DBInstance

        self.batch = batch
        self.lyricsgetter = lyricsgetter

    # ------------------------------------------------------------------
    async def run(self) -> None:
        async for session in self.db.get_session():
            try:
                for track_id in self.batch:

                    # --------------------------------------------------
                    # Load track
                    # --------------------------------------------------
                    track = await session.get_one(DBTrack, DBTrack.id == int(track_id))
                    if track is None:
                        raise DatabaseError(f"Invalid track id: {track_id}")

                    artist = (
                        track.performers[0].full_name
                        if track.performers else None
                    )
                    title = track.title

                    if not artist or not title:
                        self.logger.warning(
                            f"LyricsGetter: Track {track_id} missing artist/title"
                        )
                        continue

                    query = f"{artist} - {title}"

                    # --------------------------------------------------
                    # Fetch lyrics using injected util
                    # --------------------------------------------------
                    lyrics = await self.lyricsgetter.get_lyrics(query)

                    if lyrics:
                        obj = DBTrackLyric(Lyric=lyrics, track=track)
                        session.add(obj)

                        # update stage for each related file
                        for f in track.files:
                            self.update_file_stage(f.id, session)

                        self.set_progress()

                    else:
                        self.logger.info(f"No lyrics found for '{query}'")

                await session.commit()

            except Exception as e:
                self.logger.exception(
                    f"LyricsGetter task encountered an error: {e}"
                )

            finally:
                await session.close()
