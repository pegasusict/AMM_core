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

import pyacoustid

from ..Singletons.logger import Logger
from ..Singletons.config import Config
from ..AudioUtils.media_parser import MediaParser as Parser

class AcoustID():
    """This class generates a AcoustID fingerprint if one is needed."""
    fileinfo = {}

    def __init__(self, path:Path):
        self.config = Config()
        self.log = Logger(self.config)
        ACOUSTID_APIKEY = getenv('ACOUSTID_APIKEY')
        if not ACOUSTID_APIKEY:
            raise EnvironmentError("Environment variable 'ACOUSTID_APIKEY' is not set.")
        self.path = path

    def _scan_file(self, path):
        """
        Generates audio fingerprint.

        Args:
            path (Path): File path

        Returns:
            int, str    tracklength, fingerprint
        """
        self.duration, self.fingerprint = pyacoustid.fingerprint_file(path)

    def _get_track_info(self) -> None:
        """Retrieves track information from AcoustID Server."""
        response = pyacoustid.lookup(ACOUSTID_APIKEY, self.fingerprint, self.duration)
        if isinstance(response, dict):
            response = (response)
        for datadict in response:
            for key, value in datadict:
                if value is not None:
                    self.fileinfo[key] = value

    def process(self) -> dict:
        """Processes the given file, returning the MBID"""
        parser = Parser()
        mbid = parser
        self.fingerprint = parser.get("acoustid",False)
        self.duration = None
        if not self.fingerprint:
            self._scan_file()
        self._get_track_info()
        return {
            "mbid" : self.fileinfo["mbid"]
        }