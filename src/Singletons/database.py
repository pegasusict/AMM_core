#  Copyleft 2021-2025 Mattijs Snepvangers.
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

"""
This module contains the DB class, which is used to manage the database connection.
It uses the SQLModel library to connect to the database and perform operations on it.
"""

from typing import Any, AsyncGenerator, Callable, Awaitable, Optional
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text
from ..enums import Stage

# from ..exceptions import InvalidValueError
from ..dbmodels import DBFile, DBTask, TaskStatus
from .env_config import env_config


class DB:
    def __init__(self):
        """Initialize Async MySQL engine and session factory."""
        self.engine: AsyncEngine = create_async_engine(
            env_config.DATABASE_URL, echo=env_config.DEBUG, future=True
        )
        self.async_session_factory = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )  # type: ignore

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Async session generator for FastAPI/GraphQL Dependency Injection."""
        async with self.async_session_factory() as session:  # type: ignore
            yield session

    async def init_db(self):
        """Initialize database schema (for dev use)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    # ------------------------------------
    # DRY Core Methods
    # ------------------------------------

    async def run_in_session(
        self, func: Callable[[AsyncSession], Awaitable[Any]]
    ) -> Any:
        """Execute a coroutine within a managed async session and commit."""
        async with self.async_session_factory() as session:  # type: ignore
            result = await func(session)
            await session.commit()
            return result

    async def fetch_one(self, statement) -> Optional[Any]:
        """Fetch a single row (or None) for a SQLModel select statement."""
        async with self.async_session_factory() as session:  # type: ignore
            result = await session.exec(statement)
            return result.first()

    async def fetch_all(self, statement) -> list[Any]:
        """Fetch all rows for a SQLModel select statement."""
        async with self.async_session_factory() as session:  # type: ignore
            result = await session.exec(statement)
            return result.all()

    async def execute_raw(self, query: str):
        """Run raw SQL (text) query string."""
        return await self.run_in_session(lambda session: session.execute(text(query)))

    async def execute_stmt(self, stmt):
        """Execute SQLAlchemy statement (Insert/Update/Delete)."""
        return await self.run_in_session(lambda session: session.execute(stmt))

    # ------------------------------------
    # App Logic Methods
    # ------------------------------------

    async def set_file_stage(self, file_id: int, stage: Stage):
        """Set processing Stage for a file."""
        stmt = select(DBFile).where(DBFile.id == file_id)
        file = await self.fetch_one(stmt)
        if file:
            file.stage = stage
            await self.run_in_session(lambda session: session.merge(file))

    async def update_task_status(self, task_id: str, status: TaskStatus):
        """Update status of a task."""
        stmt = select(DBTask).where(DBTask.task_id == task_id)
        task = await self.fetch_one(stmt)
        if task:
            task.status = status
            await self.run_in_session(lambda session: session.merge(task))

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists by file path."""
        stmt = select(DBFile).where(DBFile.file_path == file_path)
        return await self.fetch_one(stmt) is not None

    async def get_paused_tasks(self) -> list[DBTask]:
        """Retrieve all tasks that are paused."""
        stmt = select(DBTask).where(DBTask.status == TaskStatus.PAUSED)
        return await self.fetch_all(stmt)


# Instantiate globally
DBInstance = DB()
