# src/core/stage_tracker.py
import datetime as dt
from typing import Any, Sequence
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from Singletons import Logger
from .enums import StageType
from .registry import stage_registry
from .dbmodels import DBFile  # your existing SQLModel DBFile

logger = Logger()


class StageTracker:
    """
    Tracks completion of individual Stage (by name) and marks StageType completed
    when all Stage instances under that StageType are done for a DBFile.

    This implementation focuses on minimal round-trips:
    - For batch updates we iterate the IDs and perform targeted update statements.
    - For MySQL/MariaDB, JSON/ARRAY append differs by backend; here we do safe per-row
      select/update to remain portable. If you want DB-specific JSON/ARRAY in-place
      updates, we can add dialect-specific code paths later.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def complete_stage_for_file(self, file_id: int, stage_name: str) -> None:
        """
        Mark a single Stage (by name) completed for a single DBFile.
        Appends stage_name to DBFile.substages if missing and marks parent StageType completed
        when all stages are done.
        """
        row = await self._fetch_file_row(file_id)
        if not row:
            logger.error(f"StageTracker: DBFile id={file_id} not found")
            return

        existing_substages, current_stage_value = row
        stage_obj = self._get_stage(stage_name)
        if not stage_obj:
            logger.error(f"StageTracker: stage '{stage_name}' not registered")
            return

        new_substages = self._append_substage(existing_substages, stage_name)
        file_stage_type = self._resolve_stage_type(current_stage_value, stage_obj.stage_type)
        stage_completed = self._is_stage_completed(file_stage_type, new_substages)

        await self._apply_stage_update(file_id, new_substages, file_stage_type, stage_completed)
        logger.info(f"Completed stage '{stage_name}' for file_id={file_id}; stage_done={stage_completed}")

    async def _fetch_file_row(self, file_id: int) -> tuple[list[str], int | None] | None:
        stmt = select(DBFile.id, DBFile.substages, DBFile.stage).where(DBFile.id == file_id)
        res = await self.session.exec(stmt)
        row = res.one_or_none()
        if not row:
            return None
        _, existing_substages, current_stage_value = row
        return (existing_substages or []), current_stage_value

    def _get_stage(self, stage_name: str) -> Any:
        return stage_registry.find_stage(stage_name)

    def _append_substage(self, existing: list[str], stage_name: str) -> list[str]:
        if stage_name in existing:
            return existing
        return list(existing) + [stage_name]

    def _resolve_stage_type(self, current_stage_value: int | None, fallback: StageType) -> StageType:
        try:
            return StageType(current_stage_value) if current_stage_value else fallback
        except Exception:
            return fallback

    def _is_stage_completed(self, stage_type: StageType, substages: list[str]) -> bool:
        required_stage_objs = stage_registry.get_stages(stage_type)
        required_names = {s.name for s in required_stage_objs}
        if not required_names:
            return True
        return required_names.issubset(set(substages))

    async def _apply_stage_update(
        self,
        file_id: int,
        substages: list[str],
        stage_type: StageType,
        stage_completed: bool,
    ) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        upd = (
            update(DBFile)
            .where(DBFile.id == file_id)
            .values(
                substages=substages,
                processed=now,
            )
        )
        if stage_completed:
            upd = upd.values(stage=int(stage_type), stage_completed=True)
        await self.session.exec(upd)
        await self.session.commit()

    async def batch_complete_stage(self, file_ids: Sequence[int], stage_name: str) -> None:
        """
        Batch-complete a named Stage for multiple files.
        For portability we loop through file_ids and call complete_stage_for_file per id.
        This is simple, robust, and works across DB backends; it's still much faster
        than loading full ORM objects for each file when using AsyncSession.
        If you need to optimize, we can add dialect-specific bulk JSON/ARRAY ops.
        """
        if not file_ids:
            return

        # For large batches, consider chunking
        CHUNK = 200
        ids = list(file_ids)
        for i in range(0, len(ids), CHUNK):
            chunk = ids[i : i + CHUNK]
            tasks = [self.complete_stage_for_file(fid, stage_name) for fid in chunk]
            # run sequentially to avoid too many concurrent DB transactions; you can use gather if your DB can handle it
            for t in tasks:
                await t

        logger.info(f"Batch completed stage '{stage_name}' for {len(file_ids)} files")
