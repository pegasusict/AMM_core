# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
#  This file is part of AMM — GPLv3+.

"""Normalizer Task — normalizes audio using injected audioutils."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from core.task_base import TaskBase, register_task
from core.types import DBInterface, GetFileTypeProtocol, NormalizeProtocol
from core.enums import TaskType, StageType, PluginType
from Singletons import Logger, DBInstance


@register_task
class Normalizer(TaskBase):
    """
    Normalizes audio files. Uses audioutils:
      - get_file_type
      - normalize
    """

    name = "normalizer"
    description = "Normalize audio loudness levels."
    version = "2.0.0"
    author = "Mattijs Snepvangers"
    plugin_type = PluginType.TASK

    task_type = TaskType.NORMALIZER
    stage_type = StageType.PROCESS
    stage_name = "process"

    # Required utilities injected by registry
    depends = ["get_file_type", "normalize"]

    # File processing: heavy operations, should not run in parallel
    exclusive: ClassVar[bool] = True
    heavy_io: ClassVar[bool] = True

    def __init__(
        self,
        *,
        batch: dict[int, str | Path],
        get_file_type: GetFileTypeProtocol,
        normalize: NormalizeProtocol,
    ) -> None:
        """
        Args:
            batch: mapping of file_id -> file_path
            get_file_type: injected util
            normalize: injected util
        """
        super().__init__()

        self.batch = {int(k): Path(v) for k, v in batch.items()}
        self.logger = Logger()
        self.db: DBInterface = DBInstance

        self.get_file_type = get_file_type
        self.normalize = normalize

    # ------------------------------------------------------------------
    async def run(self) -> None:
        async for session in self.db.get_session():
            for file_id, path in self.batch.items():

                try:
                    p = Path(path)

                    if not p.exists():
                        self.logger.error(f"Normalizer: File does not exist: {p}")
                        continue

                    # Determine type
                    file_type = await self.get_file_type(p)

                    # Run normalization (may call ffmpeg / heavy IO)
                    await self.normalize(file=p, file_type=str(file_type))

                    # Update DB stage
                    self.update_file_stage(file_id, session)

                except Exception as e:
                    self.logger.error(f"Normalization error for {path}: {e}")
                    continue

                self.set_progress()

            await session.commit()
            await session.close()
