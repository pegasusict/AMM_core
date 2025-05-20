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
from enum import Enum

from mutagen.mp4 import MP4
from mutagen.apev2 import APEv2
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wavpack import WavPack
from mutagen.asf import ASF

from src.Singletons.config import Config
from src.Singletons.logger import Logger

class FileTypes(Enum):
	"""FileType Enums"""
	MP3 = MP3
	MP4 = MP4
	FLAC = FLAC
	WAV = WavPack
	OGG = OggVorbis
	APE = APEv2
	ASF = ASF

def get_file_extension(file_path: Path) -> str:
	"""
	Returns the file extension of the media file.

	Args:
		file_path: The path to the media file.

	Returns:
		str: The file extension of the media file.
	"""
	return file_path.split('.')[-1].lower() # type: ignore


def get_file_type(file_path: Path) -> str | None:
	"""
	Returns the file type of the media file.

	Args:
		file_path: The path to the media file.

	Returns:
		str: The file type of the media file.
	"""
	file_extension = get_file_extension(file_path)
	if file_extension.upper in FileTypes:
		return file_extension
	else:
		Logger(Config()).error(message=f"Unsupported file type: {file_extension}")
		return None

