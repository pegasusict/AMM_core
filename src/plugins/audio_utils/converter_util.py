from __future__ import annotations

from pathlib import Path
from typing import Optional, ClassVar
from asyncio import to_thread

from pydub import AudioSegment

from core.audioutil_base import AudioUtilBase, register_audioutil
from Singletons import Logger
from config import Config

logger = Logger()  # singleton


@register_audioutil
class ConverterUtil(AudioUtilBase):
    name: ClassVar[str] = "converter_util"
    description: ClassVar[str] = "Converts audio files between codecs using pydub."
    version: ClassVar[str] = "1.1.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False
    heavy_io: ClassVar[bool] = True  # conversion is I/O/CPU heavy; mark accordingly

    def __init__(self) -> None:
        # registry may call with no args; accept None and use global Config
        self.config = Config.get_sync()
        # logger is the singleton — don't instantiate
        self.logger = Logger()
        self.lq_inputs = str(self.config.get("convert", "lqinputs", "ogg,aac")).split(",")
        self.hq_inputs = str(self.config.get("convert", "hqinputs", "wav,mp4")).split(",")
        self.lq_format = str(self.config.get("convert", "lqformat", "mp3")).lower()
        self.hq_format = str(self.config.get("convert", "hqformat", "flac")).lower()

    def get_target_format(self, codec: str) -> Optional[str]:
        if codec in self.lq_inputs:
            return self.lq_format
        if codec in self.hq_inputs:
            return self.hq_format
        return None

    async def convert_file(self, input_path: Path, codec: str) -> None:
        """
        Public async entrypoint. This is non-blocking: conversion runs on a thread
        via asyncio.to_thread (so it doesn't block the event loop).
        """
        await to_thread(self._convert_file_sync, input_path, codec)

    def _convert_file_sync(self, input_path: Path, codec: str) -> None:
        if not input_path.is_file():
            self.logger.info(f"Skipping {input_path}: file not found")
            return

        target_format = self.get_target_format(codec)
        if not target_format:
            self.logger.warning(f"Skipping {input_path}: no target format for {codec}")
            return

        output_path = input_path.with_suffix(f".{target_format}")
        if input_path == output_path:
            self.logger.debug(f"Skipping {input_path}: already target format")
            return

        try:
            audio = AudioSegment.from_file(input_path, format=input_path.suffix[1:].lower())
            audio.export(output_path, format=target_format)
            self.logger.info(f"Converted {input_path} -> {output_path}")
            input_path.unlink(missing_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to convert {input_path}: {e}")
