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

from pathlib import Path

from Singletons import Config, Logger
from ..enums import FileType

from .acoustid import AcoustIDClient
from .lyrics_getter import LyricsGetter
from .mb_client import MusicBrainzClient
from .media_parser import MediaParser
from .normalizer import normalize
from .tagger import Tagger
from .trimmer import SilenceTrimmer


__all__ = (
    "AcoustIDClient",
    "LyricsGetter",
    "MusicBrainzClient",
    "MediaParser",
    "normalize",
    "Tagger",
    "SilenceTrimmer",
    "get_file_extension",
    "get_file_type",
)


def get_file_extension(file_path: Path) -> str:
    """
    Returns the file extension of the media file.

    Args:
            file_path: The path to the media file.

    Returns:
            str: The file extension of the media file.
    """
    return Path(file_path).suffix.lower()


def get_file_type(file_path: Path) -> str | None:
    """
    Returns the file type of the media file.

    Args:
            file_path: The path to the media file.

    Returns:
            str: The file type of the media file, or None if unsupported.
    """
    file_extension = get_file_extension(file_path)
    # Remove the dot and convert to uppercase to match enum names
    extension_key = file_extension[1:].upper() if file_extension else ""
    if extension_key in FileType.__members__:
        return file_extension
    Logger(Config()).error(message=f"Unsupported file type: {file_extension}")
    return None
