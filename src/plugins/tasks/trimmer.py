from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Iterable, Optional

from sqlmodel import select

from core.task_base import TaskBase, register_task
from core.types import AsyncSessionLike, DBInterface, SilenceTrimmerProtocol
from core.enums import TaskType, StageType, Codec
from Singletons import DBInstance, Logger
from dbmodels import DBFile
from config import Config


@register_task
class TrimmerTask(TaskBase):
    """Trim silence from audio files using the silence_trimmer audioutil."""

    name = "trimmer"
    description = "Trims silence from audio files."
    version = "2.0.0"
    author = "Mattijs Snepvangers"

    task_type = TaskType.TRIMMER
    stage_type = StageType.PROCESS
    stage_name = "process"

    exclusive: ClassVar[bool] = False
    heavy_io: ClassVar[bool] = True

    depends = ["silence_trimmer"]

    def __init__(
        self,
        silence_trimmer: SilenceTrimmerProtocol,
        *,
        batch: Optional[Iterable[int]] = None,
        config: Optional[Config] = None,
    ) -> None:
        self.logger = Logger()
        self.config = config or Config.get_sync()
        self.db: DBInterface = DBInstance
        self.trimmer = silence_trimmer

        self.batch = list(batch or [])
        self._total = len(self.batch)
        self._processed = 0

    async def run(self) -> None:
        async for session in self.db.get_session():
            for file_id in self.batch:
                result = await session.exec(select(DBFile).where(DBFile.id == file_id))
                dbfile = result.one_or_none()
                if dbfile is None:
                    self.logger.warning(f"Trimmer: file {file_id} not found")
                    continue

                if not dbfile.file_path:
                    self.logger.warning(f"Trimmer: file {file_id} missing path")
                    continue

                file_path = Path(dbfile.file_path)
                codec = dbfile.codec
                if codec is None and file_path.suffix:
                    codec = Codec.__members__.get(file_path.suffix[1:].upper(), None)

                if codec is None:
                    self.logger.warning(f"Trimmer: unsupported codec for {file_path}")
                    continue

                try:
                    await self.trimmer.trim(file_path, codec)
                    await self.update_file_stage(dbfile.id, session)
                except Exception as e:
                    self.logger.error(f"Trimmer failed for {file_path}: {e}")

                self._processed += 1
                if self._total:
                    self.set_progress(self._processed / self._total)

            await session.commit()
            await session.close()

        self.logger.info("Trimmer task completed.")
