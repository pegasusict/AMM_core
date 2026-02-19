# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
#  Part of AMM — GPLv3+

"""Exporter Processor — copies or converts audio files to the export directory."""

from __future__ import annotations
import shutil
from pathlib import Path
from typing import ClassVar, Optional

import asyncio
from pydub import AudioSegment

from config import Config
from Singletons import Logger, DBInstance
from core.processor_base import ProcessorBase
from core.types import DBInterface
from core.registry import registry


@registry.register_processor
class Exporter(ProcessorBase):
    """
    Exports audio files to a configured directory. Converts formats if needed.
    """

    name = "exporter"
    description = "Exports files to a directory, converting formats if needed."
    version = "2.0.0"

    exclusive: ClassVar[bool] = False          # may run concurrently
    heavy_io: ClassVar[bool] = True            # filesystem + pydub conversions

    # no stage_type — processors do not advance pipeline stages

    # No util dependencies required
    depends = []

    def __init__(
        self,
        *,
        config: Optional[Config] = None,
        batch: Optional[list[int]] = None,
    ) -> None:
        super().__init__(config=config)
        self.logger = Logger()

        self.config = config or Config.get_sync()
        self.db: DBInterface = DBInstance

        self.batch = batch or []

        self.export_dir = Path(self.config.get_path("export"))
        self.export_format = self.config.get_string("export", "format", "mp3").lower()

    # ------------------------------------------------------------------
    async def run(self) -> None:
        self.export_dir.mkdir(parents=True, exist_ok=True)

        async for session in self.db.get_session():
            for track_id in self.batch:

                # Fetch DBTrack and its files
                track = await session.get_one("DBTrack", id=track_id)
                if track is None:
                    self.logger.warning(f"Exporter: Track {track_id} not found")
                    continue

                if not track.files:
                    self.logger.warning(f"Exporter: Track {track_id} has no files")
                    continue

                file = track.files[0]
                input_path = Path(file.file_path)

                if not input_path.is_file():
                    self.logger.info(f"Skipping {input_path}: File does not exist")
                    continue

                await self._export_one(input_path)

                self.set_progress()

            await session.commit()
            await session.close()

    # ------------------------------------------------------------------
    async def _export_one(self, input_path: Path) -> None:
        """
        Copies or converts the given file to the export directory.
        """

        input_ext = input_path.suffix[1:].lower()
        dst = self.export_dir / f"{input_path.stem}.{self.export_format}"

        # Direct copy
        if input_ext == self.export_format:
            try:
                await asyncio.to_thread(shutil.copy2, input_path, dst)
                self.logger.info(f"Copied: {input_path} -> {dst}")
            except Exception as e:
                self.logger.error(f"Export copy failed: {input_path}: {e}")
            return

        # Conversion via pydub
        try:
            audio = await asyncio.to_thread(AudioSegment.from_file, input_path, input_ext)
            await asyncio.to_thread(audio.export, dst, self.export_format)
            self.logger.info(f"Converted: {input_path} -> {dst}")
        except Exception as e:
            self.logger.error(f"Export conversion failed: {input_path}: {e}")
