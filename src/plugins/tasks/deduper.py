from pathlib import Path
from typing import ClassVar
from sqlmodel import select

from core.task_base import TaskBase, register_task
from core.types import DBInterface, DedupeFilesProtocol
from core.enums import TaskType, StageType
from Singletons import Logger, DBInstance
from core.dbmodels import DBTrack


@register_task
class Deduper(TaskBase):
    """
    Eliminates duplicate files based on audio quality.
    """

    name = "Deduper"
    description = "Eliminates duplicate files based on audio quality."
    version = "2.0.0"
    author = "Mattijs Snepvangers"

    task_type = TaskType.DEDUPER
    stage_type = StageType.PROCESS
    stage_name = "process"

    # required in new architecture
    exclusive: ClassVar[bool] = False        # dedupe can run in parallel
    heavy_io: ClassVar[bool] = True          # deletes files on disk

    depends = ["dedupe_files"]

    def __init__(self, dedupe_files: DedupeFilesProtocol, *, batch: list[int]) -> None:
        self.logger = Logger()
        self.batch = batch

        # injected util
        self.dedupe = dedupe_files

        self.db: DBInterface = DBInstance

        self._total = len(batch)
        self._processed = 0

    # ---------------------------------------------------------
    async def run(self) -> None:
        self.logger.info(f"Starting Deduper for {self._total} tracks.")

        async for session in self.db.get_session():

            for track_id in self.batch:

                # Load track + files
                result = await session.exec(
                    select(DBTrack)
                    .where(DBTrack.id == track_id)
                )
                track = result.one_or_none()

                if not track:
                    self.logger.warning(f"Track {track_id} not found")
                    self._processed += 1
                    self.set_progress(self._processed / self._total)
                    continue

                # Not enough files to dedupe
                if len(track.files) <= 1:
                    self.logger.info(f"Track {track_id} has no duplicates")
                    self._processed += 1
                    self.set_progress(self._processed / self._total)
                    continue

                # Run audio util
                result = await self.dedupe(track.files)
                keep = result["keep"]
                to_delete = result["delete"]

                # Delete lower-quality files
                for file in to_delete:
                    try:
                        Path(file.file_path).unlink(missing_ok=True)
                        await session.delete(file)
                        self.logger.info(f"Removed duplicate file {file.id}")
                    except Exception as e:
                        self.logger.error(f"Error deleting file {file.file_path}: {e}")

                # Mark keeper
                await self.update_file_stage(keep.id, session)

                await session.commit()

                self._processed += 1
                self.set_progress(self._processed / self._total)

            await session.close()

        self.logger.info("Deduplication completed successfully.")
        self.set_completed("Deduper finished.")
