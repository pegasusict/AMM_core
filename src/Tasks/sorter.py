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

import re
import unicodedata
from pathlib import Path

from ..Singletons.database import DB
from ..dbmodels import DBFile, Track
from task import Task
from ..Singletons.config import Config
from ..enums import TaskType, Stage
from ..Singletons.logger import Logger


class Sorter(Task):
    """Task to sort audio files into directories based on metadata."""

    batch: list[int]  # List of track IDs to sort

    def __init__(self, batch: list[int], config: Config):
        """
        Initializes the Sorter class.

        Args:
            batch: List of track IDs to sort.
            config: The configuration object.
        """
        super().__init__(config=config, task_type=TaskType.SORTER)
        self.config = config
        self.batch = batch  # type: ignore
        self.logger = Logger(config)
        self.db = DB()
        self.stage = Stage.SORTED

    def create_index_symbol(self, artist_sort: str) -> str:
        """Creates an index symbol from artist_sort, replacing non-ASCII with '0-9'."""
        initial = artist_sort[0].upper()
        norm_initial = unicodedata.normalize("NFD", initial)
        initial = "".join(
            char for char in norm_initial if unicodedata.category(char) != "Mn"
        )
        return initial if initial.isascii() and initial.isalpha() else "0-9"

    def format_number(self, number: str, count: str) -> str:
        """Formats disc/track numbers with zero-padding if necessary."""
        return "" if int(count) == 1 else f"{number.zfill(len(count))}."

    def clean_string(self, string: str) -> str:
        """Sanitizes string for filesystem usage."""
        return re.sub(r'[\/:*?"<>|]', "-", string).strip()

    def fix_duration(self, duration: int) -> str:
        """Formats duration in seconds to MM:SS."""
        minutes, seconds = divmod(duration, 60)
        return f"{minutes:02}:{seconds:02}"

    def run(self):
        """Executes the Sorter Task."""
        session = self.db.get_session()

        for track_id in self.batch:
            track = Track(track_id=track_id)  # Track assumed loaded correctly elsewhere
            result = self._prepare_track_file(track)
            if result is None:
                continue

            input_path, metadata, file_id = result
            target_path = self._build_target_path(metadata)

            if target_path.exists():
                self.logger.warning(
                    f"Target file {target_path} already exists — skipping move."
                )
                continue

            try:
                self._move_file(input_path, target_path)
                self.update_file_stage(file_id, session)
            except Exception as e:
                self.logger.error(
                    f"Failed to process {input_path} to {target_path}: {e}"
                )

            self.set_progress()

        session.commit()
        session.close()

    def _prepare_track_file(self, track):
        """Validate track and return (input_path, metadata, file_id) or None if invalid."""
        if not track.files:
            self.logger.info(f"Skipping track {track.track_id}: No files to sort.")
            return None

        file = track.files[0]
        input_path = Path(file.file_path)

        if not input_path.is_file():
            self.logger.info(f"Skipping {input_path}: File does not exist.")
            return None

        metadata = track.get_sortdata()
        if not metadata:
            self.logger.info(f"Skipping {input_path}: No metadata available.")
            return None

        return input_path, metadata, file.id

    def _build_target_path(self, metadata: dict) -> Path:
        """Build the target file path based on metadata."""
        base_path = Path(self.config.get_path("base"))

        album = self.clean_string(str(metadata.get("album", "[compilations]")))
        artist_sort = self.clean_string(
            str(metadata.get("artist_sort", "[Unknown Artist]"))
        )
        track_title = self.clean_string(str(metadata.get("title", "[Unknown Track]")))
        bitrate = str(metadata.get("bitrate", "000"))
        duration = self.fix_duration(int(metadata.get("duration", 0)))
        year = str(metadata.get("year", "0000"))

        initial = self.create_index_symbol(artist_sort)
        disc_number = self.format_number(
            str(metadata.get("disc_number", "1")), str(metadata.get("disc_count", "1"))
        )
        track_number = self.format_number(
            str(metadata.get("track_number", "1")),
            str(metadata.get("track_count", "1")),
        )

        target_dir = base_path / initial / artist_sort / f"({year}) - {album}"
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file_name = (
            f"{disc_number}{track_number} {artist_sort} - {track_title} [{bitrate}] [{duration}].mp3"
        ).strip()

        return target_dir / self.clean_string(target_file_name)

    def _move_file(self, input_path: Path, target_path: Path):
        """Move the file to the target location."""
        input_path.rename(target_path)
        self.logger.info(f"Moved {input_path} to {target_path}")
