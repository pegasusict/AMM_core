from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Iterable, Optional

from core.types import AsyncSessionLike, MediaParserProtocol, SpatializerUtilProtocol, DBInterface

from core.enums import TaskType, StageType
from core.task_base import TaskBase
from core.registry import registry
from core.dbmodels import DBFile
from Singletons import DBInstance, Logger
from config import Config


@registry.register_task
class SpatializerTask(TaskBase):
    """
    Expands stereo width by boosting the side (L-R) signal.

    Default widening is 10% (linear), applied as:
      L' = L + k*(L - R)
      R' = R + k*(R - L)
    """

    name = "spatializer"
    description = "Expands stereo width by boosting side signal."
    version = "1.0.0"
    author = "Mattijs Snepvangers"

    task_type = TaskType.CUSTOM
    stage_type = StageType.PROCESS
    stage_name = "process"

    exclusive: ClassVar[bool] = False
    heavy_io: ClassVar[bool] = True

    # Uses existing audioutils where applicable
    depends = ["media_parser", "spatializer_util"]

    def __init__(
        self,
        media_parser: MediaParserProtocol,
        spatializer_util: SpatializerUtilProtocol,
        *,
        batch: Optional[Iterable[int]] = None,
        config: Optional[Config] = None,
        widen_percent: Optional[float] = None,
    ) -> None:
        self.logger = Logger()
        self.config = config or Config.get_sync()
        self.db: DBInterface = DBInstance

        self.media_parser = media_parser
        self.spatializer = spatializer_util

        self.batch = list(batch or [])
        self._total = len(self.batch)
        self._processed = 0

        self.widen_percent = self._resolve_widen_percent(widen_percent)

    # ------------------------------------------------------------------
    async def run(self) -> None:
        async for session in self.db.get_session():
            for file_id in self.batch: # type: ignore
                await self._process_one(session, file_id)

                self._processed += 1
                if self._total:
                    self.set_progress(self._processed / self._total)

            await session.commit()
            await session.close()

        self.logger.info("Spatializer task completed.")

    # ------------------------------------------------------------------
    async def _process_one(self, session: AsyncSessionLike, file_id: int) -> None:
        dbfile = await session.get(DBFile, file_id)
        if dbfile is None:
            self.logger.warning(f"Spatializer: file {file_id} not found")
            return

        if not dbfile.file_path:
            self.logger.warning(f"Spatializer: file {file_id} missing path")
            return

        file_path = Path(dbfile.file_path)
        if not file_path.exists():
            self.logger.warning(f"Spatializer: file not found on disk: {file_path}")
            return

        if not await self._is_stereo(file_path):
            self.logger.info(f"Spatializer: skipping non-stereo file {file_path}")
            return

        try:
            if not self.spatializer:
                self.logger.error("Spatializer util not provided; aborting file.")
                return
            await self.spatializer.widen(file_path, self.widen_percent)
            await self.update_file_stage(dbfile.id, session)
        except Exception as e:
            self.logger.error(f"Spatializer failed for {file_path}: {e}")

    # ------------------------------------------------------------------
    async def _is_stereo(self, file_path: Path) -> bool:
        if not self.media_parser:
            return True

        try:
            metadata = await self.media_parser.parse(file_path)
        except Exception as e:
            self.logger.warning(f"Spatializer: metadata parse failed for {file_path}: {e}")
            return True

        channels = metadata.get("channels") if metadata else None
        return channels is None or int(channels) >= 2

    # ------------------------------------------------------------------
    def _resolve_widen_percent(self, widen_percent: Optional[float]) -> float:
        if widen_percent is not None:
            return max(0.0, float(widen_percent))

        try:
            value = self.config.get("spatializer", "width_percent", 10.0)
            return max(0.0, float(value))
        except Exception:
            return 10.0
