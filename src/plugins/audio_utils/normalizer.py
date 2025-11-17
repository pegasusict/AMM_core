# plugins/audioutil/normalizer.py
from __future__ import annotations
import asyncio
from pathlib import Path
from pydub import AudioSegment, effects

from ..core.audioutil_base import AudioUtilBase
from ..core.decorators import register_audioutil

@register_audioutil()
class Normalizer(AudioUtilBase):
    name = "normalizer"
    description = "Analyses and normalizes the audio volume using pydub."
    version = "1.0.0"
    depends: list[str] = []

    async def normalize(self, file: Path, file_type: str) -> None:
        await asyncio.to_thread(self._normalize_sync, file, file_type)

    def _normalize_sync(self, file: Path, file_type: str) -> None:
        try:
            rawsound = AudioSegment.from_file(file, file_type)
            normalizedsound = effects.normalize(rawsound)
            normalizedsound.export(file, format=file_type)
            self.logger.info(f"Normalized audio file: {file}")
        except Exception as e:
            self.logger.error(f"Error normalizing {file}: {e}", exc_info=True)
