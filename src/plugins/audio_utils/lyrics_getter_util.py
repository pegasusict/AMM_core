from __future__ import annotations

import aiohttp
from typing import ClassVar, Optional

from core.audioutil_base import AudioUtilBase, register_audioutil

from Singletons import Logger, Config


logger = Logger()  # singleton instance


@register_audioutil
class LyricsGetter(AudioUtilBase):
    """
    Unified async lyrics provider util.

    Responsibilities:
    - Provide a single async API: get_lyrics(track)
    - Fetch lyrics from a configured provider
    - Use AMM logging
    - Support dependency injection via AMM’s util registry
    """

    # --- PluginBase metadata ---
    name: ClassVar[str] = "lyricsgetter"
    description: ClassVar[str] = "Unified async lyrics provider util."
    version: ClassVar[str] = "1.1.1"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False   # safe to run concurrently
    heavy_io: ClassVar[bool] = True     # network I/O

    def __init__(self) -> None:
        self.logger = logger

        self.config = Config()
        self.provider_url = self.config.get("lyrics_provider")

        if not self.provider_url:
            self.logger.warning(
                "LyricsGetter: No 'lyrics_provider' configured; lyrics fetching disabled."
            )

    async def get_lyrics(self, track: str) -> Optional[str]:
        """
        Fetch lyrics asynchronously. `track` is a flexible string:
        Tasks may pass "artist - title" or any normalized format.
        """
        if not self.provider_url:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.provider_url}/search",
                    params={"q": track},
                ) as resp:

                    if resp.status != 200:
                        self.logger.error(
                            f"LyricsGetter: Provider returned HTTP {resp.status} for track '{track}'"
                        )
                        return None

                    data = await resp.json()
                    lyrics = data.get("lyrics")

                    if not lyrics:
                        self.logger.info(f"LyricsGetter: No lyrics found for '{track}'")

                    return lyrics

        except Exception as e:
            self.logger.exception(f"LyricsGetter: Fetch failed for '{track}': {e}")
            return None
