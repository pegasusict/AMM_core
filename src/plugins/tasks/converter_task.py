from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, Iterable, ClassVar

from core.task_base import TaskBase, register_task
from core.enums import TaskType, StageType
from Singletons import DBInstance, Logger
from config import Config
from core.types import ConverterUtilProtocol, DBInterface


@register_task
class ConverterTask(TaskBase):
    """
    Converts audio files using the injected converter_util.
    """

    name = "converter_task"
    description = "Converts audio files to target formats using pydub."
    version = "2.0.0"
    author = "Mattijs Snepvangers"

    task_type = TaskType.CONVERTER
    stage_type = StageType.CONVERT
    stage_name = "convert"

    # MUST be explicit per new rules
    exclusive: ClassVar[bool] = False         # allows multiple conversions in parallel
    heavy_io: ClassVar[bool] = True           # file reading + writing

    # Injected by registry
    depends = ["converter_util"]

    def __init__(
        self,
        converter_util: ConverterUtilProtocol,                 # always injected
        *,
        batch: Optional[Iterable[int]] = None,
        config: Optional[Config] = None,
    ) -> None:
        self.logger = Logger()

        self.config = config or Config.get_sync()
        self.batch = list(batch or [])

        # injected util
        self.converter = converter_util

        self.db: DBInterface = DBInstance

        self._total = len(self.batch)
        self._processed = 0

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    async def _get_track(self, track_id: int) -> Any:
        """
        ORM model accessor (placeholder).
        Replace with your real async ORM loader.
        """
        from core.models import Track
        return await Track.from_id(track_id)

    # ------------------------------------------------------------
    # Main async execution
    # ------------------------------------------------------------
    async def run(self) -> None:
        if not self.converter:
            self.logger.error("Converter util not provided; aborting task.")
            return

        self.logger.info(f"Starting ConverterTask for {self._total} tracks.")

        async for session in self.db.get_session():
            for track_id in self.batch:
                try:
                    track = await self._get_track(track_id)
                    if not getattr(track, "files", None):
                        self.logger.warning(f"No files for track {track_id}.")
                        self._processed += 1
                        self.set_progress(self._processed / self._total)
                        continue

                    # first file only (your existing behaviour)
                    file = track.files[0]

                    # converter_util handles thread offloading internally or via TaskManager
                    await self.converter.convert_file(Path(file.file_path), file.codec)

                    # update stage
                    await self.update_file_stage(file.id, session)

                    self._processed += 1
                    self.set_progress(self._processed / self._total)

                except Exception as e:
                    self.logger.error(f"Conversion failed for track {track_id}: {e}")

            await session.commit()
            await session.close()

        self.logger.info("Conversion task completed.")
        self.set_completed("All files converted successfully.")
