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

"""This Module exports files to a directory."""

import shutil
from pathlib import Path

from pydub import AudioSegment

from Singletons import Logger, Config
from ..dbmodels import Track
from ..enums import Codec, TaskType
from task import Task


class Exporter(Task):
    """This class is used to export files to a directory."""

    batch: list[int]  # List of track ids to export

    def __init__(self, batch: list[int], config: Config):
        """
        Initializes the Exporter class.

        Args:
            batch: Dictionary containing track ids and codec destinations.
            config: The configuration object.
        """
        super().__init__(config=config, task_type=TaskType.EXPORTER)
        self.config = config
        self.export_dir = Path(self.config.get_path("export"))
        self.export_format = self.config._get("export", "format", Codec.MP3.value)
        self.batch = batch  # type: ignore
        self.logger = Logger(config)

    def run(self):
        """Runs The Exporter Task."""
        Path.mkdir(self.export_dir, exist_ok=True, parents=True)
        for track_id in self.batch:
            track = Track(track_id=track_id)
            input_path = Path(track.files[0].file_path)

            if not input_path.is_file():
                self.logger.info(f"Skipping {input_path}: File does not exist")
                continue

            input_ext = input_path.suffix[1:].lower()
            filename_wo_ext = input_path.stem
            output_path = self.export_dir / f"{filename_wo_ext}.{self.export_format}"

            if input_ext == self.export_format:
                # Just copy the file
                try:
                    shutil.copy2(input_path, output_path)
                    self.logger.info(f"Copied: {input_path} -> {output_path}")
                except Exception as e:
                    self.logger.error(f"Failed to copy {input_path}: {e}")
            else:
                # Convert the file
                try:
                    audio = AudioSegment.from_file(input_path, format=input_ext)
                    audio.export(output_path, format=self.export_format)
                    self.logger.info(f"Converted: {input_path} -> {output_path}")
                except Exception as e:
                    self.logger.error(f"Failed to convert {input_path}: {e}")
            self.set_progress()
