# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
#  Part of AMM, GPLv3+

"""Lyrics Getter Task — new unified plugin architecture."""

from __future__ import annotations

from typing import Any, ClassVar, List, Optional

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
    version = "2.0.1"
    author = "Mattijs Snepvangers"

    task_type = TaskType.LYRICS_GETTER
    stage_type = StageType.METADATA
    stage_name = "metadata"

    depends = ["lyricsgetter"]

    # required new flags
    exclusive: ClassVar = False           # can run concurrently
    heavy_io: ClassVar = True             # network + DB operations

    def __init__(
        self,
        lyricsgetter: LyricsGetterProtocol,
        *,
        batch: List[int],
        config: Config | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(config=config, batch=batch, **kwargs)
        self.logger = Logger()
        self.config = config or Config.get_sync()
        self.db: DBInterface = DBInstance

        self.batch = batch
        self.lyricsgetter = lyricsgetter

    # ------------------------------------------------------------------
    async def run(self) -> None:
        async for session in self.db.get_session():
            try:
                for track_id in self.batch:
                    await self._process_track(session, track_id)

                await session.commit()

            except Exception as e:
                self.logger.exception(
                    f"LyricsGetter task encountered an error: {e}"
                )

            finally:
                await session.close()

    async def _process_track(self, session: Any, track_id: int) -> None:
        track = await session.get(DBTrack, int(track_id))
        if track is None:
            raise DatabaseError(f"Invalid track id: {track_id}")

        query = self._build_query(track, track_id)
        if query is None:
            return

        lyrics = await self.lyricsgetter.get_lyrics(query)
        if lyrics:
            self._store_lyrics(session, track, lyrics)
            await self._update_track_files(track, session)
            self.set_progress()
        else:
            self.logger.info(f"No lyrics found for '{query}'")

    def _build_query(self, track: DBTrack, track_id: int) -> Optional[str]:
        performers = getattr(track, "performers", None) or []
        artist = performers[0].full_name if performers else None
        title = getattr(track, "title", None)
        if not title and track.files:
            title = track.files[0].file_name
        if not artist or not title:
            self.logger.warning(
                f"LyricsGetter: Track {track_id} missing artist/title"
            )
            return None
        return f"{artist} - {title}"

    def _store_lyrics(self, session: Any, track: DBTrack, lyrics: str) -> None:
        obj = DBTrackLyric(lyric=lyrics, track=track)
        session.add(obj)

    async def _update_track_files(self, track: DBTrack, session: Any) -> None:
        for f in track.files:
            await self.update_file_stage(f.id, session)
