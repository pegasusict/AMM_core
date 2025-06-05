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
    """Trims the silences of the start and end of an audiofile."""

    file: Path | None = None
    codec: Codec | None = None
    threshold: int = -50
    chunk: int = 10
    sound: AudioSegment | None = None
    duration: int = 0
    start_trim: int = 0
    end_trim: int = 0
    trimmed_sound: AudioSegment | None = None

    def __init__(
        self, file: Path, codec: Codec, threshold: int = -50, chunk_size: int = 10
    ) -> None:
        """Initializer of the SilenceTrimmer Class.

        Args:
            file (Path):                File path to the target
            codec (Codecs):             Codec used in the file
            threshold (int, optional):  Silence threshold. Defaults to -50
            chunk_size (int, optional): Size in ms of the chunks to be processed. Defaults to 10.

        Raises:
            ValueError: Raises an error if the chunksize is smaller than 10 ms.
        """
        self.file = file
        self.codec = codec
        self.threshold = threshold
        if chunk_size < 10:
            raise ValueError("Chunksize must be at least 10 ms.")
        self.chunk = chunk_size

        self.sound = AudioSegment.from_file(self.file, format=self.codec)
        if self.sound is not None:
            self.duration = len(self.sound)
        else:
            self.duration = 0

    def _detect_silence(self, begin: bool) -> None:
        """
        iterate over chunks until you find the first one with sound.

        Arguments:
            begin: bool     Wether to trim the beginning or the end.
        """
        if self.sound is None:
            raise OperationFailedError("empty file")
        trim_ms = 0

        if begin:
            sound = self.sound
        else:
            sound = self.sound.reverse()

        while trim_ms < self.duration:
            segment = sound[trim_ms : trim_ms + self.chunk]
            if (
                not isinstance(segment, AudioSegment)
                or len(segment) == 0
                or segment.dBFS >= self.threshold
            ):
                break
            trim_ms += self.chunk

        if begin:
            self.start_trim = trim_ms
        else:
            self.end_trim = trim_ms

    def trim_silences(self):
        """Trims the silences of the start and end of an audiofile."""
        self._detect_silence(True)
        self._detect_silence(False)

        if self.sound is not None:
            self.trimmed_sound = self.sound[
                self.start_trim : self.duration - self.end_trim
            ]  # type: ignore
            # save the audio in the original format
            if self.trimmed_sound is not None:
                self.trimmed_sound.export(self.file, format=str(self.codec))
            else:
                raise OperationFailedError(
                    "Trimming resulted in no audio data to export."
                )
        else:
            self.trimmed_sound = None
            raise OperationFailedError("No audio data loaded to trim.")
