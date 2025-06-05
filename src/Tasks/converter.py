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
"""This module converts files from one codec to another."""

from pathlib import Path

from pydub import AudioSegment

from Singletons.logger import Logger
from Singletons.config import Config
from ..models import Track
from ..Enums import Codec
from task import Task, TaskType


class Converter(Task):
    """This class is used to convert files."""

    batch: list[int]  # List of track ids to convert

    def __init__(self, batch: list[int], config: Config):
        """
        Initializes the Converter class.

        Args:
            batch: Dictionary containing track ids.
            config: The configuration object.
        """
        super().__init__(config=config, task_type=TaskType.CONVERTER)
        self.config = config
        self.batch = batch  # type: ignore
        self.logger = Logger(config)
        self.lq_inputs = str(self.config.get("convert", "lqinputs", "ogg,aac")).split(
            ","
        )
        self.hq_inputs = str(self.config.get("convert", "hqinputs", "wav,mp4")).split(
            ","
        )
        self.lq_format = str(
            self.config.get("convert", "lqformat", Codec.MP3.value)
        ).lower()
        self.hq_format = str(
            self.config.get("convert", "hqformat", Codec.FLAC.value)
        ).lower()

    def run(self):
        """Runs The Converter Task."""
        for track_id in self.batch:
            track = Track(track_id=track_id)
            file = track.files[0]
            input_path = Path(file.path)

            if not input_path.is_file():
                self.logger.info(f"Skipping {input_path}: File does not exist")
                self.set_progress()
                continue

            # Determine the input quality of the file
            input_codec = file.codec
            # input_bitrate = file.bitrate
            if input_codec in self.lq_inputs:
                new_format = self.lq_format
            elif input_codec in self.hq_inputs:
                new_format = self.hq_format
            else:
                self.logger.warning(
                    f"Unknown codec or no conversion needed: {input_codec} for file {input_path}. Skipping conversion."
                )
                self.set_progress()
                continue
            input_ext = input_path.suffix[1:].lower()
            filename_wo_ext = input_path.stem
            path_wo_file = input_path.parent
            output_path = path_wo_file / f"{filename_wo_ext}.{new_format}"

            # Convert the file
            try:
                audio = AudioSegment.from_file(input_path, format=input_ext)
                audio.export(output_path, format=new_format)
                self.logger.info(f"Converted: {input_path} -> {output_path}")
                # delete the input file if the conversion was successful
                if (
                    input_path != output_path
                ):  # Avoid deleting the file if it's the same
                    input_path.unlink(missing_ok=True)
                    self.logger.info(f"Deleted original file: {input_path}")
            except Exception as e:
                self.logger.error(f"Failed to convert {input_path}: {e}")
            self.set_progress()
