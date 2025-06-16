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

"""Enum repository for the application."""

from enum import Enum, IntFlag, StrEnum, IntEnum, auto

from mutagen.mp4 import MP4
from mutagen.apev2 import APEv2
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wavpack import WavPack
from mutagen.asf import ASF


class UserRole(StrEnum):
    """Enum for user roles."""

    ADMIN = auto()
    USER = auto()
    GUEST = auto()


class TaskType(StrEnum):
    """Enum for different task types."""

    ART_GETTER = auto()
    ART_CHECKER = auto()
    IMPORTER = auto()
    TAGGER = auto()
    FINGERPRINTER = auto()
    EXPORTER = auto()
    LYRICS_GETTER = auto()
    NORMALIZER = auto()
    DEDUPER = auto()
    TRIMMER = auto()
    CONVERTER = auto()
    PARSER = auto()
    SORTER = auto()
    SCANNER = auto()
    CUSTOM = auto()
    DUPLICATE_CHECKER = auto()


class TaskStatus(StrEnum):
    """Enum for different task statuses."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    PAUSED = auto()


class Codec(StrEnum):
    """Codec types for audio files."""

    WAV = auto()
    WMA = auto()
    MP3 = auto()
    MP4 = auto()
    FLAC = auto()
    ASF = auto()
    OGG = auto()
    AAC = auto()
    APE = auto()
    AIFF = auto()
    UNKNOWN = auto()


class CodecPriority(IntEnum):
    """Priority levels for codecs."""

    FLAC = 10
    WAV = 9
    MP4 = 8
    MP3 = 7
    WMA = 6
    ASF = 5
    OGG = 3
    AAC = 4
    APE = 2
    AIFF = 1
    UNKNOWN = 0


class Stage(IntFlag):
    """Stages of processing."""

    NONE = 0
    IMPORTED = 1
    PARSED = 2
    FINGERPRINTED = 4
    DEDUPED = 8
    TRIMMED = 16
    NORMALIZED = 32
    CONVERTED = 64
    ART_RETRIEVED = 128  # Album art is needed for file
    LYRICS_RETRIEVED = 256  # Track Lyrics are needed for file
    TAGGED = 512
    SORTED = 1024


class ArtType(StrEnum):
    """Enum for different types of art."""

    ALBUM = auto()
    ARTIST = auto()
    LABEL = auto()


class MBQueryType(StrEnum):
    ARTIST = auto()
    ALBUM = auto()
    RELEASE = auto()
    TRACK = auto()
    RECORDING = auto()
    RELEASE_GROUP = auto()


class FileType(Enum):
    """FileType Enums"""

    MP3 = MP3
    MP4 = MP4
    FLAC = FLAC
    WAV = WavPack
    OGG = OggVorbis
    APE = APEv2
    ASF = ASF
