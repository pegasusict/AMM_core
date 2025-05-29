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

from os import getenv
from pathlib import Path

import acoustid
from Exceptions import FileError

from ..Singletons.logger import Logger
from ..Singletons.config import Config
from ..AudioUtils.tagger import Tagger
from ..AudioUtils.media_parser import MediaParser as Parser
from . import get_file_type


class AcoustID:
    """This class generates a AcoustID fingerprint if one is needed."""

    fileinfo = {}
    duration: int | None
    fingerprint: str | None

    def __init__(self, path: Path):
        self.config = Config()
        self.log = Logger(self.config)
        self.api_key = getenv("ACOUSTID_APIKEY")
        if not self.api_key:
            raise EnvironmentError("Environment variable 'ACOUSTID_APIKEY' is not set.")
        self.path = path

    def _scan_file(self, path: Path):
        """
        Generates audio fingerprint.

        Args:
            path (Path): File path

        Returns:
            int, str    tracklength, fingerprint
        """
        result = acoustid.fingerprint_file(path)  # type: ignore
        if isinstance(result, tuple) and len(result) == 2:
            self.duration, self.fingerprint = int(result[0]), str(result[1])
        else:
            raise RuntimeError(
                "acoustid.fingerprint_file did not return (duration, fingerprint) tuple"
            )

    def _get_track_info(self) -> None:
        """Retrieves track information from AcoustID Server."""
        response = acoustid.lookup(self.api_key, self.fingerprint, self.duration)
        score, mbid, title, artist = acoustid.parse_lookup_result(response)
        self.fileinfo["fingerprint"] = self.fingerprint
        self.fileinfo["score"] = score
        self.fileinfo["mbid"] = mbid
        self.fileinfo["title"] = title
        self.fileinfo["artist"] = artist

    def process(self) -> dict:
        """Processes the given file, returning the MBID and the fingerprint"""
        file_type = get_file_type(self.path)
        if file_type is None:
            raise FileError("Invalid or non-existing file extension")
        tagger = Tagger(self.path, file_type)
        mbid = tagger.get_mbid()
        if not mbid:
            self.fingerprint = tagger.get_acoustid()
        if not self.fingerprint:
            self._scan_file(self.path)
        elif self.duration is None:
            parser = Parser()
            self.duration = parser.get_duration(self.path)
            self._get_track_info()
        return self.fileinfo
