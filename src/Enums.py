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

from enum import StrEnum, IntEnum, auto


class UserRole(StrEnum):
    """Enum for user roles."""

    ADMIN = auto()
    USER = auto()
    GUEST = auto()


class TaskType(StrEnum):
    """Enum for different task types."""

    ART_GETTER = auto()
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


class Stage(StrEnum):
    """Stages of processing."""

    NONE = auto()
    IMPORTED = auto()
    FINGERPRINTED = auto()
    TAGS_RETRIEVED = auto()
    ART_RETRIEVED = auto()  # TODO: is Album/artist related, but album is needed for file
    LYRICS_RETRIEVED = auto()  # TODO: is track related, but needed for file...
    TRIMMED = auto()
    NORMALIZED = auto()
    TAGGED = auto()
    SORTED = auto()


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
