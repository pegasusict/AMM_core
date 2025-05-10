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

from ..models import Codecs

class SilenceTrimmer:
    """Trims the silences of the start and end of an audiofile."""
    file: Path = None
    codec: Codecs = None
    threshold: int = -50
    chunk_size: int = 10
    sound: AudioSegment = None
    duration: int = 0
    start_trim: int = 0
    end_trim: int = 0
    trimmed_sound: AudioSegment = None

    def __init__(self, file:Path, codec:Codecs, threshold:int=-50, chunk_size:int=10) -> None:
        self.file = file
        self.codec = codec
        self.threshold = threshold
        if chunk_size < 10:
            raise ValueError("Chunksize must be at least 10 ms.")
        self.chunk_size = chunk_size

        self.sound = AudioSegment.from_file(self.file, format=self.codec)
        self.duration = len(self.sound)


    def _detect_silence(self, begin: bool) -> None:
        """
        iterate over chunks until you find the first one with sound

        sound is a pydub.AudioSegment
        silence_threshold in dB
        chunk_size in ms
        """
        trim_ms = 0

        if begin:
            sound = self.sound
        else:
            sound = self.sound.reverse()

        while sound[trim_ms:trim_ms+self.chunk_size].dBFS < self.threshold and trim_ms < self.duration:
            trim_ms += self.chunk_size

        if begin:
            self.start_trim = trim_ms
        else:
            self.end_trim = trim_ms


    def trim_silences(self):
        """Trims the silences of the start and end of an audiofile."""
        self._detect_silence(True)
        self._detect_silence(False)

        self.trimmed_sound = self.sound[self.start_trim:self.duration-self.end_trim]

        # save the audio in the original format
        self.trimmed_sound.export(self.file, format=self.codec)
