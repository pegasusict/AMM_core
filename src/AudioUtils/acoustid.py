# -*- coding: utf-8 -*-
#  Copyleft 2021-2025 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  AMM is free software: you can redistribute it and/or modify  it under the terms of the
#   GNU General Public License as published by  the Free Software Foundation, either version 3
#   of the License or any later version.
#
#  AMM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with AMM.  If not, see <https://www.gnu.org/licenses/>.

"""This Module generates a Acoustid fingerprint if needed."""

from pathlib import Path
from typing import Optional, Protocol, Any
from os import getenv

from ..Exceptions import FileError, OperationFailedError


class AcoustIDClient(Protocol):
    async def fingerprint_file(self, path: Path) -> tuple[int, str]: ...
    async def lookup(self, api_key: str, fingerprint: str, duration: int) -> Any: ...
    def parse_lookup_result(self, response: Any) -> tuple[str, str, str, str]: ...


class TaggerProtocol(Protocol):
    def get_mbid(self) -> Optional[str]: ...
    def get_acoustid(self) -> Optional[str]: ...


class ParserProtocol(Protocol):
    def get_duration(self, path: Path) -> int: ...


class LoggerProtocol(Protocol):
    def info(self, message: str) -> None: ...
    def debug(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...


class AcoustID:
    """Async-capable AcoustID metadata fetcher with low complexity and high testability."""

    def __init__(
        self,
        path: Path,
        acoustid_client: AcoustIDClient,
        tagger: TaggerProtocol,
        parser: ParserProtocol,
        logger: LoggerProtocol,
        api_key: Optional[str] = None,
    ):
        self.path = path
        self.acoustid = acoustid_client
        self.tagger = tagger
        self.parser = parser
        self.log = logger
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
        self.log.debug(f"Validated extension for {self.path}")

    async def _try_get_metadata_from_tags(self) -> bool:
        mbid = self.tagger.get_mbid()
        if mbid:
            self.fileinfo["mbid"] = mbid
            self.log.info(f"MBID from tags: {mbid}")
            return True
        self.fingerprint = self.tagger.get_acoustid()
        return False

    async def _ensure_fingerprint(self) -> None:
        if self.fingerprint:
            self.log.debug("Fingerprint already available from tags.")
            return
        try:
            self.duration, self.fingerprint = await self.acoustid.fingerprint_file(
                self.path
            )
            self.log.debug(
                f"Generated fingerprint: {self.fingerprint} (duration: {self.duration})"
            )
        except Exception as e:
            self.log.error(f"Fingerprinting failed: {e}")
            raise OperationFailedError("Could not generate fingerprint.") from e

    async def _ensure_duration(self) -> None:
        if self.duration is not None:
            return
        try:
            self.duration = self.parser.get_duration(self.path)
            self.log.debug(f"Parsed duration: {self.duration}")
        except Exception as e:
            raise OperationFailedError("Failed to determine duration.") from e

    async def _lookup_metadata(self) -> None:
        try:
            response = await self.acoustid.lookup(
                self.api_key, self.fingerprint, self.duration
            )  # type: ignore
            score, mbid, title, artist = self.acoustid.parse_lookup_result(response)
        except Exception as e:
            raise OperationFailedError("Lookup failed.") from e

        if not all([score, mbid, title, artist]):
            raise OperationFailedError("Incomplete metadata from AcoustID.")

        self.fileinfo.update(
            {
                "fingerprint": self.fingerprint,
                "score": score,
                "mbid": mbid,
                "title": title,
                "artist": artist,
            }
        )
        self.log.info(f"Metadata fetched: {self.fileinfo}")
