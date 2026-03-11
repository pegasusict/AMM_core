# src/plugins/audioutil/acoustid.py
from __future__ import annotations
from pathlib import Path
import os
from typing import Optional, Any, Protocol, ClassVar

from core.audioutil_base import AudioUtilBase, register_audioutil
from Singletons import Logger
from config import Config
from core.exceptions import FileError, OperationFailedError

logger = Logger()  # singleton

class AcoustIDClient(Protocol):
    async def fingerprint_file(self, path: Path) -> tuple[int, str]:
        ...

    async def lookup(self, api_key: str, fingerprint: str, duration: int) -> Any:
        ...

    def parse_lookup_result(
        self, response: Any
    ) -> tuple[float, str, str, list[dict[str, str]]] | None:
        ...


@register_audioutil
class AcoustID(AudioUtilBase):
    # Required ClassVars (registry validation will enforce these)
    name: ClassVar[str] = "acoustid"
    description: ClassVar[str] = "Generates AcoustID fingerprints and fetches metadata."
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    depends: ClassVar[list[str]] = ["tagger", "media_parser"]  # registry will inject these
    exclusive: ClassVar[bool] = False
    heavy_io: ClassVar[bool] = True

    def __init__(self, tagger: Any = None, media_parser: Any = None, acoustid_client: Optional[AcoustIDClient] = None) -> None:
        """
        AudioUtil is instantiated by the registry. The registry will inject
        dependencies listed in `depends` (tagger, media_parser). Optionally,
        another AudioUtil (acoustid_client) may be injected too.
        """
        self.config = Config.get_sync()
        self.tagger = tagger
        self.parser = media_parser
        self._client = acoustid_client
        # API key may come from Config or environment — accept override in process()
        env_key = os.getenv("ACOUSTID_API_KEY") or os.getenv("ACOUSTID_KEY")
        self._default_api_key = env_key or self.config.get("acoustid", "api_key", "")

    async def process(self, path: Path, api_key: Optional[str] = None) -> dict[str, Any]:
        """
        Process a single file path and return metadata dict.
        This method is async and stateless; registry instantiates AcoustID once.
        """
        self._validate_extension(path)

        mbid = await self._try_get_mbid_from_tags(path)
        if mbid:
            return {"mbid": mbid}

        client = self._require_client()
        duration, fingerprint = await self._fingerprint_file(client, path)
        duration = await self._ensure_duration(duration, path)
        key = self._resolve_api_key(api_key)
        parsed = await self._lookup_metadata(client, key, fingerprint, duration)
        if not parsed:
            logger.info("AcoustID returned no matches for this file.")
            return {}

        score, mbid, title, artists = parsed
        self._validate_metadata(score, mbid, title, artists)

        return {"score": score, "mbid": mbid, "title": title, "artists": artists}

    def _validate_extension(self, path: Path) -> None:
        if not path.suffix:
            raise FileError(f"Invalid file extension: {path}")
        logger.debug(f"Validated extension for {path}")

    async def _try_get_mbid_from_tags(self, path: Path) -> Optional[str]:
        if not hasattr(self.tagger, "get_mbid"):
            return None
        try:
            mbid = await self.tagger.get_mbid(path, "")
        except Exception:
            logger.debug("Tagger.get_mbid failed; falling back to acoustic lookup")
            return None
        if mbid:
            logger.info(f"MBID from tags: {mbid}")
        return mbid

    def _require_client(self) -> AcoustIDClient:
        if self._client is None:
            raise OperationFailedError("No AcoustID client available")
        return self._client

    async def _fingerprint_file(self, client: AcoustIDClient, path: Path) -> tuple[int | None, str]:
        try:
            duration, fingerprint = await client.fingerprint_file(path)
            logger.debug(f"Generated fingerprint: {fingerprint} (duration {duration})")
            return duration, fingerprint
        except Exception as e:
            logger.error(f"Fingerprint generation failed: {e}")
            raise OperationFailedError("Could not generate fingerprint") from e

    async def _ensure_duration(self, duration: int | None, path: Path) -> int:
        if duration is not None:
            return duration
        if self.parser is not None and hasattr(self.parser, "get_duration"):
            try:
                duration = await self.parser.get_duration(path)
            except Exception as e:
                logger.debug(f"Parser get_duration failed: {e}")
        if duration is None:
            raise OperationFailedError("Could not determine file duration")
        return duration

    def _resolve_api_key(self, api_key: Optional[str]) -> str:
        key = api_key or self._default_api_key
        if not key:
            raise OperationFailedError("AcoustID API key not configured")
        return key

    async def _lookup_metadata(
        self,
        client: AcoustIDClient,
        key: str,
        fingerprint: str,
        duration: int,
    ) -> tuple[float, str, str, list[dict[str, str]]] | None:
        try:
            response = await client.lookup(key, fingerprint, duration)
            parsed = client.parse_lookup_result(response)
            return parsed
        except Exception as e:
            logger.exception("AcoustID lookup failed")
            raise OperationFailedError("Lookup failed") from e

    def _validate_metadata(
        self,
        score: float,
        mbid: str,
        title: str,
        artists: list[dict[str, str]],
    ) -> None:
        if not (mbid or title or artists):
            logger.info("AcoustID returned no usable metadata.")
