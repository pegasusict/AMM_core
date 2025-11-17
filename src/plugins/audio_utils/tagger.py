# plugins/audioutil/tagger.py
from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Optional, Any

from mutagen import MutagenError
from mutagen.apev2 import APEv2
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from mutagen.asf import ASF

from ..core.audioutil_base import AudioUtilBase
from ..core.decorators import register_audioutil
from ..singletons import Logger

@register_audioutil()
class Tagger(AudioUtilBase):
    name = "tagger"
    description = "Reads and writes tags (ID3, FLAC, OGG, APE, ASF) using Mutagen."
    version = "1.0.0"
    depends: list[str] = []

    def __init__(self, logger: Optional[Logger] = None) -> None:
        super().__init__()
        self.logger = logger or Logger()

    def _load_audio(self, file_path: Path, file_type: str):
        try:
            match file_type.upper():
                case "FLAC":
                    return FLAC(file=file_path)
                case "OGG":
                    return OggVorbis(file=file_path)
                case "APE":
                    return APEv2(file=file_path)
                case "ASF":
                    return ASF(file=file_path)
                case _:
                    return ID3(file=file_path)
        except MutagenError as e:
            self.logger.error(f"Failed to load tags for {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error loading {file_path}: {e}")
            raise

    async def get_all(self, file_path: Path, file_type: str) -> dict[str, Any]:
        return await asyncio.to_thread(self._get_all_sync, file_path, file_type)

    def _get_all_sync(self, file_path: Path, file_type: str) -> dict[str, Any]:
        audio = self._load_audio(file_path, file_type)
        return dict(audio)

    async def get(self, file_path: Path, file_type: str, tag: str) -> Optional[str]:
        return await asyncio.to_thread(self._get_sync, file_path, file_type, tag)

    def _get_sync(self, file_path: Path, file_type: str, tag: str) -> Optional[str]:
        audio = self._load_audio(file_path, file_type)
        return audio.get(tag)

    async def get_mbid(self, file_path: Path, file_type: str) -> Optional[str]:
        return await self.get(file_path, file_type, "musicbrainz_trackid") or \
               await self.get(file_path, file_type, "mbid")

    async def get_acoustid(self, file_path: Path, file_type: str) -> Optional[str]:
        return await self.get(file_path, file_type, "acoustid_id") or \
               await self.get(file_path, file_type, "acoustid")

    async def set_tag(self, file_path: Path, file_type: str, tag: str, value: str) -> None:
        await asyncio.to_thread(self._set_tag_sync, file_path, file_type, tag, value)

    def _set_tag_sync(self, file_path: Path, file_type: str, tag: str, value: str) -> None:
        audio = self._load_audio(file_path, file_type)
        audio[tag] = value
        audio.save()

    async def set_tags(
        self, file_path: Path, file_type: str, tags: dict[str, Any]
    ) -> None:
        await asyncio.to_thread(self._set_tags_sync, file_path, file_type, tags)

    def _set_tags_sync(self, file_path: Path, file_type: str, tags: dict[str, Any]) -> None:
        audio = self._load_audio(file_path, file_type)
        for tag, value in tags.items():
            audio[tag] = str(value)
        audio.save()
