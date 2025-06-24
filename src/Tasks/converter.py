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

from ..Singletons import DB, Logger, Config
from ..dbmodels import Track
from ..enums import Codec, Stage, TaskType
from task import Task


class Converter(Task):
    """This class converts audio files to target formats based on input codec."""

    def __init__(self, batch: list[int], config: Config):
        super().__init__(config=config, task_type=TaskType.CONVERTER)
        self.batch = batch
        self.logger = Logger(config)
        self.lq_inputs = config._get("convert", "lqinputs", "ogg,aac").split(",")  # type: ignore
        self.hq_inputs = config._get("convert", "hqinputs", "wav,mp4").split(",")  # type: ignore
        self.lq_format = config._get("convert", "lqformat", Codec.MP3.value).lower()  # type: ignore
        self.hq_format = config._get("convert", "hqformat", Codec.FLAC.value).lower()  # type: ignore
        self.stage = Stage.CONVERTED

    def run(self):
        """Run the conversion process."""
        db = DB()
        session = db.get_session()
        for track_id in self.batch:  # type: ignore
            track = Track(track_id)  # type: ignore
            if not track.files:
                self.logger.warning(f"No files found for track {track_id}")
                self.set_progress()
                continue

            file = track.files[0]
            self.convert_file(Path(file.file_path), file.codec)
            file_id = file.id
            self.update_file_stage(file_id, session)
            self.set_progress()
        session.commit()
        session.close()
        self.set_end_time()

    def convert_file(self, input_path: Path, codec: str) -> None:
        """Converts an audio file to the target format based on its codec.

        Checks if the file exists and is not already in the target format, then performs the conversion and deletes the original file.

        Args:
            input_path: The path to the input audio file.
            codec: The codec of the input audio file.

        Returns:
            None
        """
        if not input_path.is_file():
            self.logger.info(f"Skipping {input_path}: file does not exist")
            return

        target_format = self.get_target_format(codec)
        if not target_format:
            self.logger.warning(
                f"Skipping {input_path}: no target format for codec {codec}"
            )
            return

        output_path = input_path.with_suffix(f".{target_format}")
        if input_path == output_path:
            self.logger.info(f"Skipping {input_path}: already in target format")
            return

        try:
            audio = AudioSegment.from_file(
                input_path, format=input_path.suffix[1:].lower()
            )
            audio.export(output_path, format=target_format)
            self.logger.info(f"Converted: {input_path} -> {output_path}")
            input_path.unlink(missing_ok=True)
            self.logger.info(f"Deleted original file: {input_path}")
        except Exception as e:
            self.logger.error(f"Failed to convert {input_path}: {e}")

    def get_target_format(self, codec: str) -> str | None:
        """Determines the target audio format for a given codec.

        Returns the appropriate target format string if the codec is recognized as low or high quality input, otherwise returns None.

        Args:
            codec: The codec of the input audio file.

        Returns:
            The target format as a string, or None if the codec is not recognized.
        """
        if codec in self.lq_inputs:
            return self.lq_format
        return self.hq_format if codec in self.hq_inputs else None
