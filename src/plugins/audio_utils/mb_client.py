from __future__ import annotations

from typing import Any, ClassVar, Optional

import aiohttp
from aiohttp import ClientError

from ..core.audioutil_base import AudioUtilBase, register_audioutil
from ..core.exceptions import OperationFailedError
from ..Singletons import Logger, Config


logger = Logger  # singleton instance


@register_audioutil
class MusicBrainzClient(AudioUtilBase):
    """
    Asynchronous MusicBrainz + CoverArtArchive API client.

    Provides:
      - Artist / release / recording lookup by MBID
      - Searching by name
      - Cover art lookup
      - AcoustID audio-fingerprint metadata lookup
    """

    # --- PluginBase metadata ---
    name: ClassVar[str] = "musicbrainz_client"
    description: ClassVar[str] = "Asynchronous MusicBrainz API client."
    version: ClassVar[str] = "1.1.2"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False  # safe to run concurrently
    heavy_io: ClassVar[bool] = True    # lots of network I/O

    BASE_URL = "https://musicbrainz.org/ws/2"
    COVERART_URL = "https://coverartarchive.org"

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config=config)
        self.config = config or Config()
        self.logger = logger

        # Required User-Agent per MusicBrainz policy
        self.user_agent = (
            "Audiophiles' Music Manager/1.1 "
            "(pegasus.ict@gmail.com)"
        )

    # -------------------------
    # Internal request helpers
    # -------------------------

    async def _request(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None
    ) -> Optional[dict[str, Any]]:
        headers = {"User-Agent": self.user_agent}
        url = f"{self.BASE_URL}/{endpoint}"

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(url, params=params, timeout=20) as resp:
                    if resp.status == 200:
                        return await resp.json()

                    self.logger.warning(
                        f"MusicBrainz request failed ({resp.status}): {url}"
                    )

            except ClientError as e:
                self.logger.error(f"Network error while requesting {url}: {e}")
                raise OperationFailedError(
                    f"Network error while requesting {url}"
                ) from e

            except Exception as e:
                self.logger.exception(
                    f"Unexpected error during MusicBrainz request: {e}"
                )
                raise OperationFailedError(
                    "Unexpected MusicBrainz request error."
                ) from e

        return None

    async def _request_cover(self, mbid: str) -> Optional[str]:
        url = f"{self.COVERART_URL}/{mbid}"
        headers = {"User-Agent": self.user_agent}

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(url, timeout=20) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("images"):
                            return data["images"][0]["thumbnails"].get("large")

            except ClientError as e:
                self.logger.error(
                    f"Error retrieving cover art for {mbid}: {e}"
                )
                raise OperationFailedError(
                    "Cover art retrieval failed."
                ) from e

        return None

    # -------------------------
    # Lookup methods by ID
    # -------------------------

    async def get_artist_by_id(self, mbid: str) -> Optional[dict[str, Any]]:
        return await self._request(f"artist/{mbid}", {"fmt": "json"})

    async def get_release_by_id(self, mbid: str) -> Optional[dict[str, Any]]:
        return await self._request(f"release/{mbid}", {"fmt": "json"})

    async def get_release_group_by_id(self, mbid: str) -> Optional[dict[str, Any]]:
        return await self._request(f"release-group/{mbid}", {"fmt": "json"})

    async def get_recording_by_id(self, mbid: str) -> Optional[dict[str, Any]]:
        return await self._request(f"recording/{mbid}", {"fmt": "json"})

    async def get_track_by_id(self, mbid: str) -> Optional[dict[str, Any]]:
        return await self.get_recording_by_id(mbid)

    async def get_album_by_id(self, mbid: str) -> Optional[dict[str, Any]]:
        return await self.get_release_by_id(mbid)

    async def get_art(self, mbid: str) -> Optional[str]:
        return await self._request_cover(mbid)

    # -------------------------
    # Lookup by name
    # -------------------------

    async def get_artist_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return await self._request("artist", {"query": name, "fmt": "json"})

    async def get_album_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return await self._request("release", {"query": name, "fmt": "json"})

    async def get_track_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return await self._request("recording", {"query": name, "fmt": "json"})

    async def get_release_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return await self._request("release", {"query": name, "fmt": "json"})

    async def get_release_group_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return await self._request("release-group", {"query": name, "fmt": "json"})

    async def get_recording_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return await self._request("recording", {"query": name, "fmt": "json"})

    # -------------------------
    # AcoustID integration
    # -------------------------

    async def get_track_by_audio_fingerprint(
        self,
        fingerprint: str
    ) -> Optional[dict[str, Any]]:

        url = "https://api.acoustid.org/v2/lookup"
        params = {
            "client": self.config.get("acoustid.api_key", ""),
            "meta": "recordings+releasegroups",
            "fingerprint": fingerprint,
            "format": "json",
        }
        headers = {"User-Agent": self.user_agent}

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(url, params=params, timeout=20) as resp:
                    if resp.status == 200:
                        return await resp.json()

                    self.logger.warning(
                        f"AcoustID lookup failed ({resp.status})"
                    )

            except ClientError as e:
                self.logger.error(f"Error during AcoustID lookup: {e}")
                raise OperationFailedError(
                    "AcoustID lookup failed."
                ) from e

        return None
