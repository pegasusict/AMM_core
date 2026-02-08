#  Copyleft 2021-2026 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  AMM is free software: you can redistribute it and/or modify  it under the terms of the
#   GNU General Public License as published by  the Free Software Foundation, either version 3
#   of the License or any later version.
#
#  AMM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with AMM.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

"""
This module contains the DB class, which is used to manage the database connection.
It uses the SQLModel library to connect to the database and perform operations on it.
"""

from typing import Any, AsyncGenerator, Callable, Awaitable, Optional, TYPE_CHECKING
from pathlib import Path
import datetime as dt
import asyncio

from sqlmodel import SQLModel, select, func
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text

from core.exceptions import InvalidValueError
from Enums import ArtType, Stage, TaskStatus, TaskType
from .env_config import env_config

if TYPE_CHECKING:
    from core.types import AsyncSessionLike as DBAsyncSession
    from dbmodels import DBAlbum, DBFile, DBPerson, DBPicture, DBTask, DBLabel, DBTaskStat, DBTaskStatSnapshot
else:
    DBAsyncSession = AsyncSession


class DB:
    def __init__(self) -> None:
        """Initialize Async MySQL engine and session factory."""
        self.engine: AsyncEngine = create_async_engine(env_config.DATABASE_URL, echo=env_config.DEBUG, future=True)
        self.async_session_factory = sessionmaker(
            bind=self.engine,  # type: ignore
            class_=AsyncSession,
            expire_on_commit=False,  # type: ignore
        )

    def __call__(self) -> "DB":
        """Compatibility: allow DBInstance() usage in legacy code."""
        return self

    def _run_sync(self, coro: Awaitable[Any]) -> Any:
        """Run an async coroutine from sync code (legacy tasks)."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        # If we're already in an event loop, schedule and return immediately.
        return loop.create_task(coro)

    def set_file_stage_sync(self, file_id: int, stage: Stage) -> Any:
        return self._run_sync(self.set_file_stage(file_id, stage))

    def register_picture_sync(self, mbid: str, art_type: ArtType, save_path: Path) -> Any:
        return self._run_sync(self.register_picture(mbid, art_type, save_path))

    async def get_session(self) -> AsyncGenerator[DBAsyncSession, None]:
        """Async session generator for FastAPI/GraphQL Dependency Injection."""
        async with self.async_session_factory() as session:  # type: ignore
            yield session

    async def init_db(self) -> None:
        """Initialize database schema (for dev use)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    # DRY Core Methods

    async def run_in_session(self, func: Callable[[AsyncSession], Awaitable[Any]]) -> Any:
        """Execute a coroutine within a managed async session and commit."""
        async with self.async_session_factory() as session:  # type: ignore
            result = await func(session)
            await session.commit()
            return result

    async def fetch_one(self, statement: Any) -> Optional[Any]:
        """Fetch a single row (or None) for a SQLModel select statement."""
        async with self.async_session_factory() as session:  # type: ignore
            result = await session.exec(statement)
            return result.first()

    async def fetch_all(self, statement: Any) -> list[Any]:
        """Fetch all rows for a SQLModel select statement."""
        async with self.async_session_factory() as session:  # type: ignore
            result = await session.exec(statement)
            return result.all()

    async def execute_raw(self, query: str) -> Any:
        """Run raw SQL (text) query string."""
        return await self.run_in_session(lambda session: session.execute(text(query)))

    async def execute_stmt(self, stmt: Any) -> Any:
        """Execute SQLAlchemy statement (Insert/Update/Delete)."""
        return await self.run_in_session(lambda session: session.execute(stmt))

    # App Logic Methods

    async def set_file_stage(self, file_id: int, stage: Stage) -> None:
        """Set processing Stage for a file."""
        from dbmodels import DBFile

        stmt = select(DBFile).where(DBFile.id == file_id)
        file = await self.fetch_one(stmt)
        if file:
            file.stage = stage
            await self.run_in_session(lambda session: session.merge(file))

    async def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Update status of a task."""
        from dbmodels import DBTask

        stmt = select(DBTask).where(DBTask.task_id == task_id)
        task = await self.fetch_one(stmt)
        if task:
            task.status = status
            await self.run_in_session(lambda session: session.merge(task))

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists by file path."""
        from dbmodels import DBFile

        stmt = select(DBFile).where(DBFile.file_path == file_path)
        return await self.fetch_one(stmt) is not None

    async def get_paused_tasks(self) -> list[DBTask]:
        """Retrieve all tasks that are paused."""
        from dbmodels import DBTask

        stmt = select(DBTask).where(DBTask.status == TaskStatus.PAUSED)
        return await self.fetch_all(stmt)

    async def register_picture(self, mbid: str, art_type: ArtType, save_path: Path) -> None:
        from dbmodels import DBAlbum, DBPerson, DBLabel, DBPicture

        # determine which object needs to be retrieved
        match art_type:
            case ArtType.ALBUM:
                stmt = select(DBAlbum).where(DBAlbum.mbid == mbid)
            case ArtType.ARTIST:
                stmt = select(DBPerson).where(DBPerson.mbid == mbid)
            case _:
                stmt = select(DBLabel).where(DBLabel.mbid == mbid)
        obj = await self.fetch_one(stmt)
        if obj is None:
            raise InvalidValueError(f"DataBase: Invalid mbid {mbid} for {art_type.value}")
        match art_type:
            case ArtType.ALBUM:
                pic_obj = DBPicture(picture_path=str(save_path), album=obj)  # type: ignore
            case ArtType.ARTIST:
                pic_obj = DBPicture(picture_path=str(save_path), person=obj)  # type: ignore
            case _:
                pic_obj = DBPicture(picture_path=str(save_path), label=obj)  # type: ignore
        async for session in self.get_session():
            session.add(pic_obj)
            await session.commit()

    async def update_task_stats(
        self,
        task_type: TaskType,
        imported: int = 0,
        parsed: int = 0,
        trimmed: int = 0,
        deduped: int = 0,
    ) -> None:
        from dbmodels import DBTaskStat, DBFile

        async for session in self.get_session():
            result = await session.exec(select(DBTaskStat).where(DBTaskStat.task_type == task_type))
            stat = result.first()
            now = dt.datetime.now(dt.timezone.utc)

            if not stat:
                stat = DBTaskStat(task_type=task_type)

            stat.last_run = now
            stat.imported += imported
            stat.parsed += parsed
            stat.trimmed += trimmed
            stat.deduped += deduped

            # Recalculate playtime + filesize from DBFile
            query = select(
                func.sum(DBFile.duration),
                func.sum(DBFile.file_size),
                func.count(DBFile.id),  # type: ignore
            ).where(DBFile.stage >= Stage.IMPORTED)

            result = await session.exec(query)
            total_duration, total_filesize, total_files = result.one_or_none() or (0, 0, 0)

            stat.total_playtime = total_duration or 0
            stat.total_filesize = total_filesize or 0

            stat.average_playtime = (stat.total_playtime // total_files) if total_files else 0
            stat.average_filesize = (stat.total_filesize // total_files) if total_files else 0

            stat.updated_at = now
            session.add(stat)
            await session.commit()

    async def rebuild_all_task_stats(self) -> None:
        """Recalculate all task statistics from current file data."""
        task_types = (TaskType.IMPORTER, TaskType.PARSER, TaskType.DEDUPER, TaskType.TRIMMER)
        for task_type in task_types:
            await self._rebuild_task_type_stats(task_type)

    async def _rebuild_task_type_stats(self, task_type: TaskType) -> None:
        """Recalculate a single task type's DBTaskStat entry."""
        from dbmodels import DBTaskStat, DBFile, DBTask

        async for session in self.get_session():
            # Retrieve or create stat record
            result = await session.exec(select(DBTaskStat).where(DBTaskStat.task_type == task_type))
            stat = result.first() or DBTaskStat(task_type=task_type)

            now = dt.datetime.now(dt.timezone.utc)

            # Query DBFile for metrics (filtered by stage or task type logic)
            stmt = select(func.sum(DBFile.duration), func.sum(DBFile.file_size), func.count(DBFile.id)).where(  # type: ignore
                DBFile.task.has(DBTask.task_type == task_type)  # type: ignore
            )

            result = await session.exec(stmt)
            total_duration, total_filesize, total_files = result.one_or_none() or (0, 0, 0)

            stat.total_playtime = total_duration or 0
            stat.total_filesize = total_filesize or 0
            stat.average_playtime = (stat.total_playtime // total_files) if total_files else 0
            stat.average_filesize = (stat.total_filesize // total_files) if total_files else 0
            stat.updated_at = now
            stat.last_run = now  # this marks last full rebuild

            session.add(stat)
            await session.commit()

    async def get_task_stats(self, task_type: TaskType) -> Optional[DBTaskStat]:
        from dbmodels import DBTaskStat

        async for session in self.get_session():
            result = await session.exec(select(DBTaskStat).where(DBTaskStat.task_type == task_type))
            return result.first()

    async def snapshot_task_stats(self) -> None:
        """Store a snapshot of current task stats (e.g. daily)."""
        from dbmodels import DBTaskStatSnapshot

        async for session in self.get_session():
            for task_type in TaskType:
                stat = await self.get_task_stats(task_type)
                if stat:
                    snap = DBTaskStatSnapshot(
                        task_type=task_type,
                        snapshot_time=dt.datetime.now(dt.timezone.utc),
                        total_playtime=stat.total_playtime,
                        total_filesize=stat.total_filesize,
                        imported=stat.imported,
                        parsed=stat.parsed,
                        trimmed=stat.trimmed,
                        deduped=stat.deduped,
                    )
                    session.add(snap)
            await session.commit()

    async def get_task_stat_snapshots(self, task_type: TaskType) -> Optional[list[DBTaskStatSnapshot]]:
        from dbmodels import DBTaskStatSnapshot

        async for session in self.get_session():
            result = await session.exec(
                select(DBTaskStatSnapshot)
                .where(DBTaskStatSnapshot.task_type == task_type)
                .order_by(
                    DBTaskStatSnapshot.snapshot_time  # type: ignore
                )
            )
            return result.all() if result else None  # type: ignore


# Instantiate globally
DBInstance = DB()
