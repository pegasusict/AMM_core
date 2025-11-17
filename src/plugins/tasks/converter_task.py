# plugins/task/converter_task.py
from __future__ import annotations
from pathlib import Path
from typing import Optional, Iterable

from ..core.decorators import register_task
from ..core.task_base import TaskBase
from ..core.enums import TaskType, StageType
from ..singletons import DBInstance, Logger, Config
# from ..core.registry import registry  # if you need to fetch utils by name at runtime

@register_task()
class ConverterTask(TaskBase):
    name: str = "converter_task"
    description: str = "Converts audio files to target formats using pydub."
    task_type = TaskType.CONVERTER
    stage_type = StageType.CONVERT
    depends: list[str] = ["converter_util"]

    def __init__(
        self,
        converter_util: Optional[object] = None,  # injected as first positional arg by registry
        *,
        batch: Optional[Iterable[int]] = None,
        config: Optional[Config] = None,
    ) -> None:
        cfg = config or Config()
        super().__init__(config=cfg, batch=list(batch) if batch else [], logger=Logger(cfg))
        self.converter = converter_util
        self.logger = Logger(cfg)

    # Allow post-construction injection if needed
    def set_converter_util(self, util: object) -> None:
        self.converter = util

    async def run(self):
        if not self.converter:
            self.logger.error("Converter util not available; aborting conversion task.")
            return

        async for session in DBInstance.get_session():
            for track_id in self.batch:
                try:
                    # Track model access — replicate your previous behaviour
                    track = await self._get_track(track_id)
                    if not getattr(track, "files", None):
                        self.logger.warning(f"No files found for track {track_id}")
                        self.set_progress()
                        continue

                    file = track.files[0]
                    await self.converter.convert_file(Path(file.file_path), file.codec)
                    # update stage in DB — reuse your existing helper
                    await self.update_file_stage(file.id, session)  # implement update_file_stage on TaskBase or here
                    self.set_progress()
                except Exception as e:
                    self.logger.error(f"Conversion failed for track {track_id}: {e}")

            await session.commit()
            await session.close()
            self.set_end_time_to_now()

    # Example helper (adapt to your DB models)
    async def _get_track(self, track_id: int):
        # adapt to your ORM; placeholder to match previous code
        from ..core.models import Track
        return Track(track_id)
