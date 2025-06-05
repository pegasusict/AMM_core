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
        norm_initial = unicodedata.normalize('NFD', initial)
        # Remove diacritical marks (category Mn = "Mark, Nonspacing")
        initial = ''.join(char for char in norm_initial if unicodedata.category(char) != 'Mn')
        # make sure initial is an ascii letter without accents
        if not initial.isascii() or not initial.isalpha():
            return "0-9"
        return initial

    def get_number_width(self, number: str, count: str) -> tuple[str, int]:
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
        return str(number).zfill(width), width

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
                self.logger.info(
                    f"Skipping {input_path}: No metadata available for sorting"
                )
                continue
            # Determine the target directory based on metadata and configuration
            base_path = Path(self.config.get_path("base"))

            album = str(metadata.get("album", "[compilations]"))
            artist_sort = str(metadata.get("artist_sort", "[Unknown Artist]"))
            track_title = str(metadata.get("title", "[Unknown Track]"))
            bitrate = str(metadata.get("bitrate", "000"))
            duration = int(metadata.get("duration", 0))
            year = str(metadata.get("year", "0000"))

            # Create an index symbol based on the artist_sort
            initial = self.create_index_symbol(artist_sort)
            # Ensure the artist_sort is a valid directory name
            artist_sort = artist_sort.replace("/", "-").replace("\\", "-").replace(":", "-")
            # Ensure the album name is a valid directory name
            album = album.replace("/", "-").replace("\\", "-").replace(":", "-")
            # Get year, disc number, and track number from metadata

            disc_number, disc_width = self.get_number_width(str(metadata.get("disc_number", "1")), str(metadata.get("disc_count", "1")))
            disc_number = disc_number + "." if disc_width > 0 else ""
            tracknumber, track_width = self.get_number_width(str(metadata.get("track_number", "1")), str(metadata.get("track_count", "1")))
            tracknumber = tracknumber + ". " if track_width > 0 else ""

            if duration > 60:
                duration = f"{duration // 60:02}_{duration % 60:02}"


            target_dir = base_path / initial / artist_sort / f"({year}) - {album}"
            # Create the target directory if it doesn't exist
            target_dir.mkdir(parents=True, exist_ok=True)
            # Construct the target file path
            target_file = target_dir / f"{disc_number}{tracknumber}{artist_sort} - {track_title} [{bitrate}] [{duration}].mp3"
            # Move the file to the target directory
            try:
                input_path.rename(target_file)
                self.logger.info(f"Moved {input_path} to {target_file}")
            except Exception as e:
                self.logger.error(f"Failed to move {input_path} to {target_file}: {e}")
            self.set_progress()
