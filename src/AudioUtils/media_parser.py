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
from typing import Any

from mutagen import File

from mutagen.id3._util import ID3NoHeaderError
from mutagen.flac import FLACNoHeaderError

from Singletons.config import Config
from Singletons.logger import Logger
from AudioUtils import get_file_type, get_file_extension


class MediaParser:
    """
    This class is used to parse media files and extract metadata from them.
    It uses the mutagen library to read and write metadata to media files.
    """

    def __init__(self, config: Config = Config()):
        """Initializes the MediaParser class."""
        self.config = config
        self.logger = Logger(config)

    def parse(self, file_path: Path) -> dict[str, str | int | Path | None] | None:
        """Parses the media file and returns the metadata."""
        file_type = get_file_type(file_path)
        if file_type is None:
            return None
        metadata: dict[str, str | int | Path | None] = {}
        try:
            self._set_metadata(file_path, metadata, file_type)
        except (ID3NoHeaderError, FLACNoHeaderError) as e:
            self.logger.error(f"Error parsing file {file_path}: {e}")
            return None

        return metadata

    def _set_metadata(self, file_path, metadata, file_type):
        metadata["bitrate"] = self.get_bitrate(file_path)
        metadata["duration"] = self.get_duration(file_path)
        metadata["sample_rate"] = self.get_sample_rate(file_path)
        metadata["channels"] = self.get_channels(file_path)
        metadata["codec"] = self.get_codec(file_path)
        metadata["file_type"] = file_type
        metadata["file_size"] = Path.stat(file_path).st_size
        metadata["file_path"] = file_path
        metadata["file_name"] = str(file_path).split("/")[-1].split(".")[0]
        metadata["file_extension"] = get_file_extension(file_path)

    def _safe(self, attr: Any, default: Any = "") -> Any:
        """Acts as a safetynet for attributes that may not exist."""
        return attr if attr is not None else default

    def _get_audio_info_from_file(self, file_path: Path, key: str) -> str | int | None:
        """
        Returns the audio file object from the media file.
        Args:
                file_path: The path to the media file.
        Returns:
                File: The audio file object.
        """
        try:
            audio = File(file_path)  # type: ignore
            result = self._safe(getattr(audio.info, key), None)  # type: ignore

            # if result is a number in a string or a float, convert to an integer
            if (isinstance(result, str) and result.isdigit()) or isinstance(
                result, float
            ):
                result = int(result)
            return result
        except Exception as e:
            self.logger.error(
                f"Error getting audio info '{key}' from file {file_path}: {e}"
            )
            return None

    def get_bitrate(self, file_path: Path) -> int | None:
        """
        Returns the bitrate of the media file.
        Args:
                file_path: The path to the media file.
        Returns:
                int: The bitrate of the media file.
        """
        return self._get_audio_info_from_file(file_path, "bitrate")  # type: ignore

    def get_duration(self, path: Path) -> int:
        """
        Returns the duration in seconds of the media file.
        Args:
                file_path: The path to the media file.
        Returns:
                int: The duration of the media file.
        """
        return self._get_audio_info_from_file(path, "duration")  # type: ignore

    def get_sample_rate(self, file_path: Path) -> int | None:
        """
        Returns the sample rate of the media file.
        Args:
                file_path: The path to the media file.
        Returns:
                int: The sample rate of the media file.
        """
        return self._get_audio_info_from_file(file_path, "sample_rate")  # type: ignore

    def get_channels(self, file_path: Path) -> int | None:
        """
        Returns the number of channels of the media file.
        Args:
                file_path: The path to the media file.
        Returns:
                int: The number of channels of the media file.
        """
        return self._get_audio_info_from_file(file_path, "channels")  # type: ignore

    def get_codec(self, file_path: Path) -> str | None:
        """
        Returns the codec of the media file.
        Args:
                file_path: The path to the media file.
        Returns:
                str: The codec of the media file.
        """
        return self._get_audio_info_from_file(file_path, "codec")  # type: ignore
