# src/core/stage_tracker.py
import datetime as dt
from typing import Sequence
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from ..singletons import Logger
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

    def __init__(self, session: AsyncSession):
        self.session = session

    async def complete_stage_for_file(self, file_id: int, stage_name: str):
        """
        Mark a single Stage (by name) completed for a single DBFile.
        Appends stage_name to DBFile.substages if missing and marks parent StageType completed
        when all stages are done.
        """
        # minimal select to fetch needed columns
        stmt = select(DBFile.id, DBFile.substages, DBFile.stage).where(DBFile.id == file_id)
        res = await self.session.exec(stmt)
        row = res.one_or_none()
        if not row:
            logger.error(f"StageTracker: DBFile id={file_id} not found")
            return

        _, existing_substages, current_stage_value = row
        existing_substages = existing_substages or []

        # find Stage metadata
        stage_obj = stage_registry.find_stage(stage_name)
        if not stage_obj:
            logger.error(f"StageTracker: stage '{stage_name}' not registered")
            return

        # Append stage_name if not present
        if stage_name not in existing_substages:
            new_substages = list(existing_substages) + [stage_name]
        else:
            new_substages = existing_substages

        # Determine the stage_type to check. Prefer the current file.stage if set,
        # otherwise use the stage object's stage_type.
        try:
            file_stage_type = StageType(current_stage_value) if current_stage_value else stage_obj.stage_type
        except Exception:
            file_stage_type = stage_obj.stage_type

        # Evaluate completion: gather all stage names under this stage_type
        required_stage_objs = stage_registry.get_stages(file_stage_type)
        required_names = {s.name for s in required_stage_objs}

        stage_completed = False
        if required_names:
            if required_names.issubset(set(new_substages)):
                stage_completed = True
        else:
            # if no registered stages under that StageType, the act of completing this stage marks it done
            stage_completed = True

        now = dt.datetime.now(dt.timezone.utc)

        # Build update statement
        upd = (
            update(DBFile)
            .where(DBFile.id == file_id)
            .values(
                substages=new_substages,
                processed=now,
            )
        )

        if stage_completed:
            upd = upd.values(stage=int(file_stage_type), stage_completed=True)

        await self.session.exec(upd)
        await self.session.commit()
        logger.info(f"Completed stage '{stage_name}' for file_id={file_id}; stage_done={stage_completed}")

    async def batch_complete_stage(self, file_ids: Sequence[int], stage_name: str):
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
