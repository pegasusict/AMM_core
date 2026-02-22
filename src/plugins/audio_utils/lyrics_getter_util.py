from __future__ import annotations

import asyncio
import os
import re
from typing import Any, ClassVar

try:
    import lyricsgenius
except ModuleNotFoundError:  # pragma: no cover
    lyricsgenius = None  # type: ignore[assignment]

from config import Config
from core.audioutil_base import AudioUtilBase, register_audioutil
from Singletons import Logger

logger = Logger()  # singleton instance


@register_audioutil
class LyricsGetter(AudioUtilBase):
    """
    Unified async lyrics util backed by the Genius API.

    Responsibilities:
      - Provide a single async API: get_lyrics(track)
      - Fetch lyrics using the `lyricsgenius` client
      - Keep network I/O off the event loop
    """

    # --- PluginBase metadata ---
    name: ClassVar[str] = "lyricsgetter"
    description: ClassVar[str] = "Unified async lyrics provider util."
    version: ClassVar[str] = "1.2.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False   # safe to run concurrently
    heavy_io: ClassVar[bool] = True     # network I/O

    _EMBED_RE = re.compile(r"\s*\d*Embed\s*$", re.IGNORECASE)

    def __init__(self) -> None:
        self.logger = logger

        self.config = Config.get_sync()
        self.genius_token = (
            self.config.get("genius_api_token")
            or self.config.get("genius_access_token")
            or os.getenv("GENIUS_ACCESS_TOKEN")
            or os.getenv("GENIUS_API_TOKEN")
        )
        self.client: Any | None = None

        if lyricsgenius is None:
            self.logger.warning(
                "LyricsGetter: 'lyricsgenius' dependency not available; "
                "lyrics fetching disabled."
            )
            return

        if not self.genius_token:
            self.logger.warning(
                "LyricsGetter: No Genius token configured "
                "(genius_api_token or GENIUS_ACCESS_TOKEN)."
            )
            return

        self.client = lyricsgenius.Genius(  # type: ignore[union-attr]
            self.genius_token,
            verbose=False,
            timeout=15,
            retries=2,
            remove_section_headers=True,
            skip_non_songs=True,
            excluded_terms=["(Remix)", "(Live)"],
        )

    async def get_lyrics(self, track: str) -> str | None:
        """
        Fetch lyrics asynchronously using Genius.
        `track` can be "artist - title" or a free-form query.
        """
        if not self.client:
            return None

        query = (track or "").strip()
        if not query:
            return None

        artist, title = self._split_query(query)

        try:
            lyrics = await asyncio.to_thread(self._search_lyrics, artist, title)

            if not lyrics:
                self.logger.info(f"LyricsGetter: No lyrics found for '{query}'")
                return None

            return self._clean_lyrics(lyrics)

        except Exception as e:
            self.logger.exception(f"LyricsGetter: Fetch failed for '{query}': {e}")
            return None

    def _search_lyrics(self, artist: str | None, title: str) -> str | None:
        if not self.client:
            return None
        song = self.client.search_song(title=title, artist=artist)
        if song is None:
            song = self.client.search_song(title=title)
        return getattr(song, "lyrics", None)

    @staticmethod
    def _split_query(query: str) -> tuple[str | None, str]:
        if " - " in query:
            artist, _, title = query.partition(" - ")
            if title.strip():
                return artist.strip() or None, title.strip()
        return None, query

    @classmethod
    def _clean_lyrics(cls, lyrics: str) -> str | None:
        cleaned = cls._EMBED_RE.sub("", lyrics or "").strip()
        return cleaned or None
