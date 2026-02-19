
from typing import Any

from sqlmodel import func, select

from core.enums import StageType, TaskType
from core.processor_base import ProcessorBase
from core.registry import registry
from core.dbmodels import DBFile
from core.exceptions import DatabaseError
from Singletons import DBInstance, Logger


@registry.register_processor
class DuplicateScanProcessor(ProcessorBase):
    """
    Processor that scans the database for duplicate files
    and emits a deduplication stage.
    """

    stage_type = StageType.PREPROCESS
    stage_name = "Duplicate Scan Processor"
    name = "duplicate_scan_processor"
    description = "Scans the database for duplicate files and emits a deduplication stage."
    version = "1.0.0"
    exclusive = True
    heavy_io = True
    depends = []

    def __init__(self, *, config: Any = None) -> None:
        super().__init__(config=config)
        self.db = DBInstance
        self.logger = Logger()

    async def run(self) -> None:
        try:
            stmt = (
                select(DBFile.track_id)
                .group_by(DBFile.track_id)
                .having(func.count(DBFile.id) > 1)
            )

            duplicate_track_ids: list[Any] = await self.db.fetch_all(stmt)

        except Exception as exc:
            self.logger.exception("Duplicate scan failed")
            raise DatabaseError("Failed to scan for duplicate files") from exc

        if not duplicate_track_ids:
            self.logger.info("No duplicate files found")
            return

        track_ids = [row for row in duplicate_track_ids]

        self.logger.info(
            f"Duplicate files detected: {len(track_ids)} tracks with duplicates",
        )

        # Emit a dedupe task for the duplicate tracks
        self.emit_task(task_type=TaskType.DEDUPER, batch=track_ids)
