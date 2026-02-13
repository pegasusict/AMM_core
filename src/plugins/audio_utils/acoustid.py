# src/plugins/audioutil/acoustid.py
from __future__ import annotations
from pathlib import Path
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

    def parse_lookup_result(self, response: Any) -> tuple[int, str, str, dict] | None:
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
        self._default_api_key = self.config.get("acoustid", "api_key", None)

    async def process(self, path: Path, api_key: Optional[str] = None) -> dict[str, Any]:
        """
        Process a single file path and return metadata dict.
        This method is async and stateless; registry instantiates AcoustID once.
        """
        self._validate_extension(path)

        # try tags first (if tagger supports it)
        if hasattr(self.tagger, "get_mbid"):
            try:
                mbid = await self.tagger.get_mbid(path, "")
                if mbid:
                    logger.info(f"MBID from tags: {mbid}")
                    return {"mbid": mbid}
            except Exception:
                # tagger failure shouldn't stop us
                logger.debug("Tagger.get_mbid failed; falling back to acoustic lookup")

        # fingerprint / duration
        fingerprint = None
        duration = None

        # prefer client injected via DI
        client = self._client
        if client is None:
            raise OperationFailedError("No AcoustID client available")

        try:
            duration, fingerprint = await client.fingerprint_file(path)
            logger.debug(f"Generated fingerprint: {fingerprint} (duration {duration})")
        except Exception as e:
            logger.error(f"Fingerprint generation failed: {e}")
            raise OperationFailedError("Could not generate fingerprint") from e

        # ensure duration from parser if missing
        if duration is None and self.parser is not None and hasattr(self.parser, "get_duration"):
            try:
                duration = await self.parser.get_duration(path)
            except Exception as e:
                logger.debug(f"Parser get_duration failed: {e}")

        if duration is None:
            raise OperationFailedError("Could not determine file duration")

        # lookup
        key = api_key or self._default_api_key
        if not key:
            raise OperationFailedError("AcoustID API key not configured")

        try:
            response = await client.lookup(key, fingerprint, duration)
            parsed = client.parse_lookup_result(response)
            if not parsed:
                raise OperationFailedError("Lookup returned no results")
            score, mbid, title, artists = parsed
        except Exception as e:
            logger.exception("AcoustID lookup failed")
            raise OperationFailedError("Lookup failed") from e

        if not all([score, mbid, title, artists]):
            raise OperationFailedError("Incomplete metadata from AcoustID")

        return {"score": score, "mbid": mbid, "title": title, "artists": artists}

    def _validate_extension(self, path: Path) -> None:
        if not path.suffix:
            raise FileError(f"Invalid file extension: {path}")
        logger.debug(f"Validated extension for {path}")
