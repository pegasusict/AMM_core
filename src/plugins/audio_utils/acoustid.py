# plugins/audioutil/acoustid.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, Any, Protocol
from os import getenv

from ..core.audioutil_base import AudioUtilBase
from ..core.decorators import register_audioutil
from ..singletons import Logger
from ..core.exceptions import FileError, OperationFailedError

logger = Logger()


class AcoustIDClient(Protocol):
    async def fingerprint_file(self, path: Path) -> tuple[int, str]:
        ...

    async def lookup(self, api_key: str, fingerprint: str, duration: int) -> Any:
        ...

    def parse_lookup_result(self, response: Any) -> tuple[int, str, str, dict] | None:
        ...


@register_audioutil()
class AcoustID(AudioUtilBase):
    name: str = "acoustid"
    description: str = "Generates AcoustID fingerprints and fetches metadata."
    version: str = "1.0.0"
    depends: list[str] = ["tagger", "media_parser"]

    def __init__(
        self,
        path: Path,
        acoustid_client: AcoustIDClient,
        tagger: Any,
        media_parser: Any,
        api_key: Optional[str] = None,
    ):
        # Note: in practice the registry will inject tagger/media_parser instances
        super().__init__()
        self.path = path
        self.acoustid = acoustid_client
        self.tagger = tagger
        self.parser = media_parser
        self.api_key = api_key or getenv("ACOUSTID_APIKEY")
        if not self.api_key:
            raise EnvironmentError("ACOUSTID_APIKEY is not set in environment.")

        self.duration: Optional[int] = None
        self.fingerprint: Optional[str] = None
        self.fileinfo: dict[str, str | None] = {}

    async def process(self) -> dict[str, str | None]:
        self._validate_extension()
        if await self._try_get_metadata_from_tags():
            return self.fileinfo
        await self._ensure_fingerprint()
        await self._ensure_duration()
        await self._lookup_metadata()
        return self.fileinfo

    def _validate_extension(self) -> None:
        if not self.path.suffix:
            raise FileError(f"Invalid file extension: {self.path}")
        logger.debug(f"Validated extension for {self.path}")

    async def _try_get_metadata_from_tags(self) -> bool:
        if mbid := await self.tagger.get_mbid(self.path, "") if hasattr(self.tagger, "get_mbid") else None:
            self.fileinfo["mbid"] = mbid
            logger.info(f"MBID from tags: {mbid}")
            return True
        # If the tagger can provide acoustid tag
        if hasattr(self.tagger, "get_acoustid"):
            self.fingerprint = await self.tagger.get_acoustid(self.path, "")
        return False

    async def _ensure_fingerprint(self) -> None:
        if self.fingerprint:
            logger.debug("Fingerprint already available from tags.")
            return
        try:
            self.duration, self.fingerprint = await self.acoustid.fingerprint_file(self.path)
            logger.debug(f"Generated fingerprint: {self.fingerprint} (duration: {self.duration})")
        except Exception as e:
            logger.error(f"Fingerprinting failed: {e}")
            raise OperationFailedError("Could not generate fingerprint.") from e

    async def _ensure_duration(self) -> None:
        if self.duration is not None:
            return
        try:
            self.duration = await self.parser.get_duration(self.path)
            logger.debug(f"Parsed duration: {self.duration}")
        except Exception as e:
            raise OperationFailedError("Failed to determine duration.") from e

    async def _lookup_metadata(self) -> None:
        try:
            response = await self.acoustid.lookup(self.api_key, self.fingerprint, self.duration)
            parsed = self.acoustid.parse_lookup_result(response)
            if not parsed:
                raise OperationFailedError("Lookup returned no results.")
            score, mbid, title, artists = parsed
        except Exception as e:
            raise OperationFailedError("Lookup failed.") from e

        if not all([score, mbid, title, artists]):
            raise OperationFailedError("Incomplete metadata from AcoustID.")

        self.fileinfo.update(
            {"score": score, "mbid": mbid, "title": title, "artists": artists}
        )
