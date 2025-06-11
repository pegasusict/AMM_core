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
from ..dbmodels import Track
from ..Enums import Codec
from task import Task, TaskType


class Converter(Task):
    """This class converts audio files to target formats based on input codec."""

    def __init__(self, batch: list[int], config: Config):
        super().__init__(config=config, task_type=TaskType.CONVERTER)
        self.batch = batch
        self.logger = Logger(config)
        self.lq_inputs = config.get("convert", "lqinputs", "ogg,aac").split(",")  # type: ignore
        self.hq_inputs = config.get("convert", "hqinputs", "wav,mp4").split(",")  # type: ignore
        self.lq_format = config.get("convert", "lqformat", Codec.MP3.value).lower()  # type: ignore
        self.hq_format = config.get("convert", "hqformat", Codec.FLAC.value).lower()  # type: ignore

    def run(self):
        for track_id in self.batch:  # type: ignore
            track = Track(track_id)  # type: ignore
            if not track.files:
                self.logger.warning(f"No files found for track {track_id}")
                self.set_progress()
                continue

            self.convert_file(Path(track.files[0].path), track.files[0].codec)
            self.set_progress()

    def convert_file(self, input_path: Path, codec: str) -> None:
        if not input_path.is_file():
            self.logger.info(f"Skipping {input_path}: file does not exist")
            return

        target_format = self.get_target_format(codec)
        if not target_format:
            self.logger.warning(f"Skipping {input_path}: no target format for codec {codec}")
            return

        output_path = input_path.with_suffix(f".{target_format}")
        if input_path == output_path:
            self.logger.info(f"Skipping {input_path}: already in target format")
            return

        try:
            audio = AudioSegment.from_file(input_path, format=input_path.suffix[1:].lower())
            audio.export(output_path, format=target_format)
            self.logger.info(f"Converted: {input_path} -> {output_path}")
            input_path.unlink(missing_ok=True)
            self.logger.info(f"Deleted original file: {input_path}")
        except Exception as e:
            self.logger.error(f"Failed to convert {input_path}: {e}")

    def get_target_format(self, codec: str) -> str | None:
        if codec in self.lq_inputs:
            return self.lq_format
        if codec in self.hq_inputs:
            return self.hq_format
        return None
