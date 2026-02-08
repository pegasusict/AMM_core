from __future__ import annotations

import asyncio
import math
from pathlib import Path
from typing import ClassVar

from pydub import AudioSegment

from core.audioutil_base import AudioUtilBase, register_audioutil
from Singletons import Logger


logger = Logger()  # singleton instance


@register_audioutil
class SpatializerUtil(AudioUtilBase):
    """
    Expands stereo width by boosting the side (L-R) signal.
    """

    name: ClassVar[str] = "spatializer_util"
    description: ClassVar[str] = "Expands stereo width by boosting side signal."
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False
    heavy_io: ClassVar[bool] = True

    def __init__(self) -> None:
        self.logger = logger

    # -----------------------------------------------------
    # Public async API
    # -----------------------------------------------------
    async def widen(self, file: Path, widen_percent: float = 10.0) -> None:
        await asyncio.to_thread(self._widen_sync, file, widen_percent)

    # -----------------------------------------------------
    # Synchronous worker (runs in thread)
    # -----------------------------------------------------
    def _widen_sync(self, file: Path, widen_percent: float) -> None:
        if widen_percent <= 0:
            self.logger.info(f"Spatializer: widen_percent=0, skipping {file}")
            return

        if not file.is_file():
            raise FileNotFoundError(f"File not found: {file}")

        file_format = file.suffix.lstrip(".").lower()
        if not file_format:
            raise ValueError(f"Unsupported file type for {file}")

        audio = AudioSegment.from_file(file, format=file_format)
        if audio.channels != 2:
            self.logger.info(f"Spatializer: non-stereo audio, skipping {file}")
            return

        k = widen_percent / 100.0
        gain_db = self._linear_gain_to_db(k)

        left, right = audio.split_to_mono()

        diff_lr = left.overlay(right.invert_phase())
        diff_lr = diff_lr.apply_gain(gain_db)
        left_out = left.overlay(diff_lr)

        diff_rl = right.overlay(left.invert_phase())
        diff_rl = diff_rl.apply_gain(gain_db)
        right_out = right.overlay(diff_rl)

        widened = AudioSegment.from_mono_audiosegments(left_out, right_out)

        if widened.max_dBFS > 0:
            widened = widened.apply_gain(-widened.max_dBFS)

        widened.export(file, format=file_format)
        self.logger.info(f"Spatializer: widened {file} by {widen_percent:.1f}%")

    def _linear_gain_to_db(self, linear_gain: float) -> float:
        if linear_gain <= 0:
            return -120.0
        return 20.0 * math.log10(linear_gain)
