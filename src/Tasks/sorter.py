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
"""This module sorts files based on their metadata."""

import unicodedata
from pathlib import Path

from ..models import Track
from task import Task
from ..Singletons.config import Config
from ..Enums import TaskType
from ..Singletons.logger import Logger


class Sorter(Task):
    """This class is used to sort files based on their metadata."""

    batch: list[int]  # List of track ids to sort

    def __init__(self, batch: list[int], config: Config):
        """
        Initializes the Sorter class.

        Args:
            batch: List of track ids to sort.
            config: The configuration object.
        """
        super().__init__(config=config, task_type=TaskType.SORTER)
        self.config = config
        self.batch = batch  # type: ignore
        self.logger = Logger(config)

    def create_index_symbol(self, artist_sort: str) -> str:
        """
        Creates an index symbol for the artist_sort.

        Args:
            artist_sort: The artist_sort string.

        Returns:
            A single character index symbol.
        """
        initial = str(artist_sort)[0].upper()
        # Normalize to NFD (decomposes characters)
        norm_initial = unicodedata.normalize("NFD", initial)
        # Remove diacritical marks (category Mn = "Mark, Nonspacing")
        initial = "".join(char for char in norm_initial if unicodedata.category(char) != "Mn")
        # make sure initial is an ascii letter without accents
        if not initial.isascii() or not initial.isalpha():
            return "0-9"
        return initial

    def format_number(self, number: str, count: str) -> str:
        """
        Determines the width of the number based on the count.
        Args:
            number: The number to format.
            count: The total count of items.
        Returns:
            A tuple containing the formatted number and its width.
        """
        if count == "1":
            number = ""
            width = 0
        else:
            width = len(str(count))
        number = str(number).zfill(width)
        number = number + "." if width > 0 else ""
        return number

    def clean_string(self, string: str) -> str:
        """
        Cleans a string to make it suitable for use as a directory name.

        Args:
            string: The string to clean.

        Returns:
            A cleaned string with invalid characters replaced.
        """
        return string.replace("/", "-").replace("\\", "-").replace(":", "-").strip()

    def fix_duration(self, duration: int) -> str:
        """
        Fixes the duration format to always be 2 digits.

        Args:
            duration: The duration in seconds.

        Returns:
            A string representing the duration in MM:SS format.
        """
        minutes = duration // 60
        seconds = duration % 60
        return f"{minutes:02}:{seconds:02}"

    def run(self):
        """Runs The Sorter Task."""
        for track_id in self.batch:
            track = Track(track_id=track_id)
            if not track.files:
                self.logger.info(f"Skipping track {track_id}: No files to sort")
                continue
            input_path = Path(track.files[0].path)
            if not input_path.is_file():
                self.logger.info(f"Skipping {input_path}: File does not exist")
                continue
            # Get metadata needed for sorting
            metadata = track.get_sortdata()
            if not metadata:
                self.logger.info(f"Skipping {input_path}: No metadata available for sorting")
                continue
            # Determine the target directory based on metadata and configuration
            base_path = Path(self.config.get_path("base"))

            album = str(metadata.get("album", "[compilations]"))
            artist_sort = str(metadata.get("artist_sort", "[Unknown Artist]"))
            track_title = str(metadata.get("title", "[Unknown Track]"))
            bitrate = str(metadata.get("bitrate", "000"))
            duration = int(metadata.get("duration", 0))
            year = str(metadata.get("year", "0000"))

            initial = self.create_index_symbol(artist_sort)
            artist_sort = self.clean_string(artist_sort)
            album = self.clean_string(album)
            # Get year, disc number, and track number from metadata

            disc_number = self.format_number(
                str(metadata.get("disc_number", "1")),
                str(metadata.get("disc_count", "1")),
            )
            track_number = self.format_number(
                str(metadata.get("track_number", "1")),
                str(metadata.get("track_count", "1")),
            )

            duration = self.fix_duration(duration)

            target_dir = base_path / initial / artist_sort / f"({year}) - {album}"
            # Create the target directory if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)
            # Construct the target file path
            target_file = (f"{disc_number}{track_number} {artist_sort} - {track_title} [{bitrate}] [{duration}].mp3").strip()
            target_file = target_dir / self.clean_string(target_file)
            # Move the file to the target directory
            try:
                input_path.rename(target_file)
                self.logger.info(f"Moved {input_path} to {target_file}")
            except Exception as e:
                self.logger.error(f"Failed to move {input_path} to {target_file}: {e}")
            self.set_progress()
