# tasks/deduper_task.py

from pathlib import Path

from sqlmodel import select

from ..core.decorators import register_task
from ..core.task_base import TaskBase
from ..core.enums import TaskType, StageType
from ..dbmodels import DBTrack
from ..Singletons import Logger, DBInstance


@register_task
class Deduper(TaskBase):
    """
    Eliminates duplicate files based on audio quality.
    """

    name = "Deduper"
    description = "Eliminates duplicate files based on audio quality."
    version = "1.0.0"
    task_type = TaskType.DEDUPER
    stage_type = StageType.DEDUPED
    depends = ["dedupe_files"]

    def __init__(self, config, batch: list[int]):
        super().__init__(config=config)
        self.batch = batch
        self.logger = Logger(config)

    async def run(self):
        """
        Runs the task.
        """
        async for session in DBInstance.get_session():

            for track_id in self.batch:

                # --- Load track + files
                result = session.exec(
                    select(DBTrack)
                    .where(DBTrack.id == track_id)
                    .options(DBTrack.files)  # eager load
                )
                track = result.one_or_none()

                if not track:
                    self.logger.warning(f"Track {track_id} not found")
                    continue

                if len(track.files) <= 1:
                    self.logger.info(f"Track {track_id} has no duplicates")
                    self.set_progress()
                    continue

                # --- Run audio util
                result = await self.dedupe_files(track.files)
                keep = result["keep"]
                to_delete = result["delete"]

                # --- Delete lower quality files
                for file in to_delete:
                    try:
                        Path(file.file_path).unlink(missing_ok=True)
                        await session.delete(file)
                        self.logger.info(f"Removed duplicate file {file.id}")
                    except Exception as e:
                        self.logger.error(f"Error deleting file {file.file_path}: {e}")

                # --- Mark the keeper
                self.update_file_stage(keep.id, session)

                await session.commit()
                self.set_progress()

        self.logger.info("Deduplication complete")
