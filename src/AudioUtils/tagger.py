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

"""Write and read tags of songs."""

from pathlib import Path

from mutagen.apev2 import APEv2
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from mutagen.asf import ASF
from collections.abc import Iterable

# from ..Singletons.config import Config
# from ..Singletons.logger import Logger

class Tagger():
    """Reads and writes tags in audiofiles."""

    def __init__(self, file_path:Path, file_type:str):
        self.file_path = file_path
        self.file_type = file_type

        match file_type:
            case "FLAC":
                self.audio = FLAC(file=self.file_path)
            case "OGG":
                self.audio = OggVorbis(file=self.file_path)
            case "APE":
                self.audio = APEv2(file=self.file_path)
            case "ASF":
                self.audio = ASF(file=self.file_path)
            case _:
                self.audio = ID3(file=self.file_path)

    def get_mbid(self) -> str|None:
        """Retrieve the MBid tag if it exists."""
        return self.audio["mbid"] or None

    def get_acoustid(self) -> str|None:
        """Retrieve the acoustid tag if it exists."""
        return self.audio["acoustid"] or None

    def get_all(self) -> dict:
        """Retrieve all tags as a dictionary."""
        return dict(self.audio)

    def get(self, tag:str) -> str|None:
        """Retrieve the requested Tag or None if not available."""
        return self.audio[tag] or None

    def set_tag(self, tag: str, value: str) -> None:
        """Set the value of a tag and save to file."""
        self.audio[tag] = value
        self.audio.save()

    def set_tags(self, tags: Iterable[tuple[str, str]]) -> None:
        """Sets the value of several tags and save to file"""
        for tag, value in tags:
            self.audio[tag] = value
        self.audio.save()
