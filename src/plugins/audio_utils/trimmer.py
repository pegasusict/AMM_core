# plugins/audioutil/silence_trimmer.py
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import ClassVar

from pydub import AudioSegment

from core.audioutil_base import AudioUtilBase, register_audioutil
from core.exceptions import OperationFailedError
from core.dbmodels import Codec
from Singletons import Logger


logger = Logger()  # singleton instance


@register_audioutil
class SilenceTrimmer(AudioUtilBase):
    """
    Trims leading and trailing silence from audio files using pydub.
    """

    # ---- PluginBase metadata ----
    name: ClassVar[str] = "silence_trimmer"
    description: ClassVar[str] = "Trims leading and trailing silence using pydub."
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False   # can run concurrently
    heavy_io: ClassVar[bool] = True     # loads + exports full audio files

    def __init__(self) -> None:
        self.logger = logger

    # -----------------------------------------------------
    # Public async API
    # -----------------------------------------------------

    async def trim(
        self,
        file: Path,
        codec: Codec,
        threshold: int = -50,
        chunk_size: int = 10,
        dry_run: bool = False,
    ) -> None:
        """Async-safe trim wrapper."""
        await asyncio.to_thread(
            self._trim_sync,
            file,
            codec,
            threshold,
            chunk_size,
            dry_run,
        )

    # -----------------------------------------------------
    # Synchronous worker (runs in thread)
    # -----------------------------------------------------

    def _trim_sync(
        self,
        file: Path,
        codec: Codec,
        threshold: int,
        chunk_size: int,
        dry_run: bool,
    ) -> None:

        if chunk_size < 10:
            raise ValueError("Chunk size must be at least 10 ms.")

        if not file.is_file():
            raise FileNotFoundError(f"File not found: {file}")

        try:
            sound = AudioSegment.from_file(file, format=str(codec))
        except Exception as e:
            raise OperationFailedError(f"Failed to load audio: {e}") from e

        duration = len(sound)
        if duration == 0:
            raise OperationFailedError("Audio file is empty.")

        start_trim = self._detect_silence_boundary(sound, duration, threshold, chunk_size)
        end_trim = self._detect_silence_boundary(sound.reverse(), duration, threshold, chunk_size)

        if end_trim <= start_trim:
            raise OperationFailedError("Trimming would remove all audio data.")

        trimmed = sound[start_trim : duration - end_trim]

        self.logger.info(
            f"Trimming {start_trim} ms at start and {end_trim} ms at end of {file}"
        )

        if dry_run:
            self.logger.info("Dry run: export skipped.")
            return

        try:
            trimmed.export(file, format=str(codec))
            self.logger.info(f"Trimmed file successfully exported: {file}")
        except Exception as e:
            raise OperationFailedError(f"Failed to export trimmed audio: {e}") from e

    # -----------------------------------------------------
    # Silence detection
    # -----------------------------------------------------

    def _detect_silence_boundary(
        self,
        sound: AudioSegment,
        duration: int,
        threshold: int,
        chunk_size: int,
    ) -> int:
        trim_ms = 0

        while trim_ms < duration:
            segment = sound[trim_ms : trim_ms + chunk_size]

            if len(segment) == 0 or segment.dBFS >= threshold:  # type: ignore
                break

            trim_ms += chunk_size

        return trim_ms
