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

"""Trims silences of start and end of songs."""

from pathlib import Path
from pydub import AudioSegment

from ..Exceptions import OperationFailedError
from ..models import Codec


class SilenceTrimmer:
    """Trims the silences from the start and end of an audio file."""

    def __init__(
        self,
        file: Path,
        codec: Codec,
        threshold: int = -50,
        chunk_size: int = 10,
        dry_run: bool = False,
    ) -> None:
        """
        Initialize the SilenceTrimmer.

        Args:
            file (Path): Path to the audio file.
            codec (Codec): The codec/format of the file.
            threshold (int): Silence threshold in dBFS. Defaults to -50.
            chunk_size (int): Chunk size in milliseconds. Defaults to 10.
            dry_run (bool): If True, do not export changes. Defaults to False.
        """
        if chunk_size < 10:
            raise ValueError("Chunk size must be at least 10 ms.")
        if not file.is_file():
            raise FileNotFoundError(f"File not found: {file}")

        self.file: Path = file
        self.codec: Codec = codec
        self.threshold: int = threshold
        self.chunk: int = chunk_size
        self.dry_run: bool = dry_run

        try:
            self.sound: AudioSegment = AudioSegment.from_file(file, format=str(codec))
        except Exception as e:
            raise OperationFailedError(f"Failed to load audio: {e}")

        self.duration: int = len(self.sound)
        self.start_trim: int = 0
        self.end_trim: int = 0
        self.trimmed_sound: AudioSegment | None = None

    def _detect_silence_boundary(self, reverse: bool = False) -> int:
        """
        Detect silence length from one end.

        Args:
            reverse (bool): If True, scans from end of file.

        Returns:
            int: Milliseconds of silence detected.
        """
        sound = self.sound.reverse() if reverse else self.sound
        trim_ms = 0

        while trim_ms < self.duration:
            segment = sound[trim_ms : trim_ms + self.chunk]
            if len(segment) == 0 or segment.dBFS >= self.threshold:  # type: ignore
                break
            trim_ms += self.chunk

        return trim_ms

    def get_trim_times(self) -> tuple[int, int]:
        """
        Calculate and return the leading and trailing silence durations.

        Returns:
            tuple[int, int]: start_trim_ms, end_trim_ms
        """
        self.start_trim = self._detect_silence_boundary()
        self.end_trim = self._detect_silence_boundary(reverse=True)
        return self.start_trim, self.end_trim

    def trim_silences(self) -> None:
        """Trim leading and trailing silence. If not dry_run, overwrite the file."""
        if self.duration == 0:
            raise OperationFailedError("Audio file is empty.")

        start, end = self.get_trim_times()
        if end <= start:
            raise OperationFailedError("Trimming would remove all audio data.")

        self.trimmed_sound = self.sound[start : self.duration - end]  # type: ignore

        if self.dry_run:
            return  # Skip export in dry-run mode

        try:
            self.trimmed_sound.export(self.file, format=str(self.codec))  # type: ignore
        except Exception as e:
            raise OperationFailedError(f"Failed to export trimmed audio: {e}")
