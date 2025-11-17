# plugins/audioutil/media_parser.py
from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Any, Optional

from mutagen import File
from mutagen.id3._util import ID3NoHeaderError
from mutagen.flac import FLACNoHeaderError

from ..core.audioutil_base import AudioUtilBase
from ..core.decorators import register_audioutil
from ..singletons import Config, Logger
from ..core.file_utils import get_file_type, get_file_extension

@register_audioutil()
class MediaParser(AudioUtilBase):
    name = "media_parser"
    description = "Parses media files and extracts bitrate, duration, codec, and more."
    version = "1.0.1"
    depends: list[str] = []

    def __init__(self, config: Optional[Config] = None):
        super().__init__(config=config)
        self.config = config or Config()
        self.logger = Logger(self.config)

    async def parse(self, file_path: Path) -> Optional[dict[str, Any]]:
        file_type = get_file_type(file_path)
        if file_type is None:
            self.logger.warning(f"Unsupported file type for: {file_path}")
            return None

        try:
            metadata: dict[str, Any] = await self._gather_metadata(file_path, file_type)
            return metadata
        except (ID3NoHeaderError, FLACNoHeaderError) as e:
            self.logger.error(f"Failed to parse {file_path}: {e}")
            return None
        except Exception as e:
            self.logger.exception(f"Unexpected error parsing {file_path}: {e}")
            return None

    async def _gather_metadata(self, file_path: Path, file_type: str) -> dict[str, Any]:
        loop = asyncio.get_running_loop()

        metadata_tasks = {
            "bitrate": loop.run_in_executor(None, self.get_bitrate, file_path),
            "duration": loop.run_in_executor(None, self.get_duration, file_path),
            "sample_rate": loop.run_in_executor(None, self.get_sample_rate, file_path),
            "channels": loop.run_in_executor(None, self.get_channels, file_path),
            "codec": loop.run_in_executor(None, self.get_codec, file_path),
        }

        results = await asyncio.gather(*metadata_tasks.values(), return_exceptions=True)

        metadata = {
            key: (val if not isinstance(val, Exception) else None)
            for key, val in zip(metadata_tasks.keys(), results)
        }

        metadata.update(
            {
                "file_type": file_type,
                "file_size": file_path.stat().st_size,
                "file_path": str(file_path),
                "file_name": file_path.stem,
                "file_extension": get_file_extension(file_path),
            }
        )

        return metadata

    def _safe_get(self, attr: Any, default: Any = None) -> Any:
        return attr if attr is not None else default

    def _get_audio_info_from_file(self, file_path: Path, key: str) -> Any:
        try:
            audio = File(file_path)
            if not audio or not hasattr(audio, "info"):
                return None

            result = getattr(audio.info, key, None)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return self._safe_get(result)
        except Exception as e:
            self.logger.debug(f"Could not get '{key}' from {file_path}: {e}")
            return None

    def get_bitrate(self, file_path: Path) -> Optional[int]:
        return self._get_audio_info_from_file(file_path, "bitrate")

    def get_duration(self, file_path: Path) -> Optional[int]:
        return self._get_audio_info_from_file(file_path, "length") or \
               self._get_audio_info_from_file(file_path, "duration")

    def get_sample_rate(self, file_path: Path) -> Optional[int]:
        return self._get_audio_info_from_file(file_path, "sample_rate")

    def get_channels(self, file_path: Path) -> Optional[int]:
        return self._get_audio_info_from_file(file_path, "channels")

    def get_codec(self, file_path: Path) -> Optional[str]:
        return self._get_audio_info_from_file(file_path, "codec")
