# plugins/audioutil/normalizer.py
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import ClassVar

from pydub import AudioSegment, effects

from ..core.audioutil_base import AudioUtilBase, register_audioutil
from ..singletons import Logger

logger = Logger  # singleton instance


@register_audioutil
class Normalizer(AudioUtilBase):
    """
    Audio volume normalizer using pydub.

    Performs:
      - Loading audio file
      - Applying pydub normalization
      - Rewriting the normalized audio back to disk
    """

    # ----- PluginBase metadata -----
    name: ClassVar[str] = "normalizer"
    description: ClassVar[str] = "Analyses and normalizes the audio volume using pydub."
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False   # can run concurrently
    heavy_io: ClassVar[bool] = True     # reads/writes full audio files

    def __init__(self):
        self.logger = logger

    # ------------------------------
    # Public API
    # ------------------------------

    async def normalize(self, file: Path, file_type: str) -> None:
        """Async wrapper that moves CPU- and I/O-heavy work into a thread."""
        await asyncio.to_thread(self._normalize_sync, file, file_type)

    # ------------------------------
    # Sync worker
    # ------------------------------

    def _normalize_sync(self, file: Path, file_type: str) -> None:
        try:
            raw = AudioSegment.from_file(file, file_type)
            normalized = effects.normalize(raw)
            normalized.export(file, format=file_type)

            self.logger.info(f"Normalized audio file: {file}")

        except Exception as e:
            self.logger.error(
                f"Error normalizing {file}: {e}",
                exc_info=True
            )
