# -*- coding: utf-8 -*-
#  Copyleft 2021-2024 Mattijs Snepvangers.
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


import os
from mutagen import File
from mutagen.mp4 import MP4
from mutagen.apev2 import APEv2
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wavpack import WavPack
from mutagen.asf import ASF
from mutagen.id3 import ID3NoHeaderError
from mutagen.flac import FLACNoHeaderError
from ..Singletons.config import Config
from ..Singletons.Logger import Logger

class MediaParser:
	"""
	This class is used to parse media files and extract metadata from them.
	It uses the mutagen library to read and write metadata to media files.
	"""

	def __init__(self, config:Config):
		"""
		Initializes the MediaParser class.

		Args:
			config: The configuration object.
		"""
		self.config = config
		self.file_types = {
			'mp3': MP3,
			'mp4': MP4,
			'flac': FLAC,
			'wav': WavPack,
			'ogg': OggVorbis,
			'ape': APEv2,
			'asf': ASF
		}

	def parse(self, file_path) -> dict:
		"""
		Parses the media file and returns the metadata.

		Args:
			file_path: The path to the media file.

		Returns:
			dict: A dictionary containing the metadata.
		"""
		file_type = self.get_file_type(file_path)
		if file_type is None:
			return None
		metadata={}
		try:
			metadata['bitrate'] = self.get_bitrate(file_path)
			metadata['duration'] = self.get_duration(file_path)
			metadata['sample_rate'] = self.get_sample_rate(file_path)
			metadata['channels'] = self.get_channels(file_path)
			metadata['codec'] = self.get_codec(file_path)
			metadata['file_type'] = file_type
			metadata['file_size'] = self.get_file_size(file_path)
			metadata['file_path'] = file_path
			metadata['file_name'] = self.get_file_name(file_path)
			metadata['file_extension'] = self.get_file_extension(file_path)

		except (ID3NoHeaderError, FLACNoHeaderError) as e:
			Logger.error(f"Error parsing file {file_path}: {e}")
			return None

		return metadata

	def get_file_type(self, file_path) -> str:
		"""
		Returns the file type of the media file.

		Args:
			file_path: The path to the media file.

		Returns:
			str: The file type of the media file.
		"""
		file_extension = self.get_file_extension(file_path)
		if file_extension in self.file_types:
			return file_extension
		else:
			Logger.error(f"Unsupported file type: {file_extension}")
			return None

	def get_file_extension(self, file_path) -> str:
		"""
		Returns the file extension of the media file.

		Args:
			file_path: The path to the media file.

		Returns:
			str: The file extension of the media file.
		"""
		return file_path.split('.')[-1].lower()

	def get_file_name(self, file_path) -> str:
		"""
		Returns the file name of the media file.
		Args:
			file_path: The path to the media file.
		Returns:
			str: The file name of the media file.
		"""
		return file_path.split('/')[-1].split('.')[0]

	def get_file_size(self, file_path) -> int:
		"""
		Returns the file size of the media file.
		Args:
			file_path: The path to the media file.
		Returns:
			int: The file size of the media file.
		"""
		return os.path.getsize(file_path)

	def get_bitrate(self, file_path) -> int:
		"""
		Returns the bitrate of the media file.
		Args:
			file_path: The path to the media file.
		Returns:
			int: The bitrate of the media file.
		"""
		audio = File(file_path)
		if audio is not None:
			return audio.info.bitrate
		else:
			Logger.error(f"Error getting bitrate for file {file_path}")
			return None

	def get_duration(self, file_path) -> float:
		"""
		Returns the duration of the media file.
		Args:
			file_path: The path to the media file.
		Returns:
			float: The duration of the media file.
		"""
		audio = File(file_path)
		if audio is not None:
			return audio.info.length
		else:
			Logger.error(f"Error getting duration for file {file_path}")
			return None

	def get_sample_rate(self, file_path) -> int:
		"""
		Returns the sample rate of the media file.
		Args:
			file_path: The path to the media file.
		Returns:
			int: The sample rate of the media file.
		"""
		audio = File(file_path)
		if audio is not None:
			return audio.info.sample_rate
		else:
			Logger.error(f"Error getting sample rate for file {file_path}")
			return None

	def get_channels(self, file_path) -> int:
		"""
		Returns the number of channels of the media file.
		Args:
			file_path: The path to the media file.
		Returns:
			int: The number of channels of the media file.
		"""
		audio = File(file_path)
		if audio is not None:
			return audio.info.channels
		else:
			Logger.error(f"Error getting channels for file {file_path}")
			return None

	def get_codec(self, file_path) -> str:
		"""
		Returns the codec of the media file.
		Args:
			file_path: The path to the media file.
		Returns:
			str: The codec of the media file.
		"""
		audio = File(file_path)
		if audio is not None:
			return audio.info.codec
		else:
			Logger.error(f"Error getting codec for file {file_path}")
			return None
