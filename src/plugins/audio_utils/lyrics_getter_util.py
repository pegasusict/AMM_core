from amm.core.registry import register_audioutil
from ..Singletons import Logger, Config
import aiohttp

logger = Logger()


@register_audioutil()
class LyricsGetter:
    """
    Unified async lyrics provider util.

    Responsibilities:
    - Provide a single async API: get_lyrics(track)
    - Fetch lyrics from a configured provider
    - Use AMM logging
    - Support dependency injection via AMM’s util registry
    """
    name = "lyricsgetter"
    description = "Unified async lyrics provider util."
    version = "1.0.0"
    # declare optional util dependencies here
    depends = []

    def __init__(self, config:Config):
        self.config = config
        self.provider_url = self.config.get("lyrics_provider")

        if not self.provider_url:
            logger.warning(
                "LyricsGetter: No 'lyrics_provider' configured; lyrics fetching disabled."
            )

    async def get_lyrics(self, track: str) -> str | None:
        """
        Fetch lyrics asynchronously. Track is a string; your tasks may pass
        title/artist combined or a normalized dict depending on your project.
        """
        if not self.provider_url:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.provider_url}/search",
                    params={"q": track}
                ) as resp:

                    if resp.status != 200:
                        logger.error(
                            "LyricsGetter: Provider returned HTTP %s for track '%s'",
                            resp.status, track
                        )
                        return None

                    data = await resp.json()
                    lyrics = data.get("lyrics")

                    if not lyrics:
                        logger.info("LyricsGetter: No lyrics found for '%s'", track)

                    return lyrics

        except Exception as e:
            logger.exception("LyricsGetter: Fetch failed for '%s': %s", track, e)
            return None
