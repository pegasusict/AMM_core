# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
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

from enum import Enum, StrEnum, IntEnum, auto, IntFlag

from mutagen.mp4 import MP4
from mutagen.apev2 import APEv2
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wavpack import WavPack
from mutagen.asf import ASF


class AppStatus(StrEnum):
    """Enum to indicate te state of the application"""

    DEVELOPMENT = auto()
    TESTING = auto()
    PRODUCTION = auto()


class UserRole(StrEnum):
    """Enum for user roles."""

    ADMIN = auto()
    MOD = auto()
    USER = auto()
    GUEST = auto()

class StageType(IntFlag):
    """Enum for Stage Types."""

    NONE = 0
    PREIMPORT = 1
    IMPORT = 2          # importer
    POSTIMPORT = 4      
    PREANALYSE = 8
    ANALYSE = 16        # fingerprinter
    POSTANALYSE = 32
    PREPROCESS = 64     # duplicate scanner,
    PROCESS = 128       # normalizer, trimmer
    POSTPROCESS = 256
    PRECONVERT = 512
    CONVERT = 1024      # converter
    POSTCONVERT = 2048
    PREMETADATA = 4096
    METADATA = 8192     # metadata getter, artgetter, lyrics getter
    POSTMETADATA = 16384
    PRETAGWRITE = 32768
    TAGWRITE = 65536    # tagger
    POSTTAGWERITE = 131072
    PRESORT = 262144
    SORT = 524288       # sorter
    POSTSORT = 1048576


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


class PluginType(StrEnum):
    """Enum for plugin types."""

    AUDIOUTIL = auto()
    PROCESSOR = auto()
    TASK = auto()


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


class TagType(StrEnum):
    """Defines Tag Types."""

    UNKNOWN = auto()
    TITLE = auto()
    SUBTITLE = auto()
    TITLESORT = auto()
