from typing import Optional

import strawberry
from strawberry.types import Info
from sqlmodel import func, select

from ..enums import TaskType
from ..dbmodels import (
    DBTask,
    DBTrack,
    DBAlbum,
    DBPerson,
    DBGenre,
    DBLabel,
    DBFile,
    DBUser,
)
from ..Singletons.database import DBInstance
from .schemas import (
    DisplayTask,
    Paginated,
    StatDelta,
    StatPoint,
    TaskStatSummary,
    TaskStatTrend,
    TaskStats,
    Track,
    Album,
    Person,
    Genre,
    Label,
    FileType,
    User,
)
from .mapping import (
    map_dbtask_to_displaytask,
    map_dbtrack_to_track,
    map_dbalbum_to_album,
    map_dbperson_to_person,
    map_dbgenre_to_genre,
    map_dblabel_to_label,
    map_dbuser_to_user,
)


@strawberry.type
class Query:
    """GraphQL Queries to retrieve Tracks, Albums, Persons, Genres."""

    @strawberry.field
    async def get_track(self, info: Info, track_id: int) -> Optional[Track]:
        """Fetch a single track by ID."""
        async for session in DBInstance.get_session():
            track = await session.get(DBTrack, track_id)
            return map_dbtrack_to_track(track) if track else None

    @strawberry.field
    async def get_album(self, info: Info, album_id: int) -> Optional[Album]:
        """Fetch a single album by ID."""
        async for session in DBInstance.get_session():
            album = await session.get(DBAlbum, album_id)
            return map_dbalbum_to_album(album) if album else None

    @strawberry.field
    async def get_person(self, info: Info, person_id: int) -> Optional[Person]:
        """Fetch a single person (artist) by ID."""
        async for session in DBInstance.get_session():
            person = await session.get(DBPerson, person_id)
            return map_dbperson_to_person(person) if person else None

    @strawberry.field
    async def get_genre(self, info: Info, genre_id: int) -> Optional[Genre]:
        """Fetch a single genre by ID."""
        async for session in DBInstance.get_session():
            genre = await session.get(DBGenre, genre_id)
            return map_dbgenre_to_genre(genre) if genre else None

    @strawberry.field()
    async def get_task_display(self, info: Info) -> Optional[list[DisplayTask]]:
        """Fetches a list of tasks."""
        async for session in DBInstance.get_session():
            tasks = await session.get(DBTask, None)
            return [map_dbtask_to_displaytask(task) for task in tasks] if tasks else None  # type: ignore

    @strawberry.field
    async def task_stats(self, info: Info, task_type: TaskType) -> Optional[TaskStats]:
        stat = await DBInstance.get_task_stats(task_type)
        return TaskStats(**stat.dict()) if stat else None

    @strawberry.field
    async def task_stat_trend(self, info: Info, task_type: TaskType) -> Optional[TaskStatTrend]:
        snapshots = await DBInstance.get_task_stat_snapshots(task_type)
        if not snapshots:
            return None

        def build_series(field: str) -> list[StatPoint]:
            return [StatPoint(timestamp=s.snapshot_time, value=getattr(s, field) or 0) for s in snapshots]

        return TaskStatTrend(
            task_type=task_type,
            imported=build_series("imported"),
            parsed=build_series("parsed"),
            trimmed=build_series("trimmed"),
            deduped=build_series("deduped"),
            total_playtime=build_series("total_playtime"),
            total_filesize=build_series("total_filesize"),
        )

    @strawberry.field
    async def task_stat_summary(self, info: Info, task_type: TaskType) -> Optional[TaskStatSummary]:
        snapshots = await DBInstance.get_task_stat_snapshots(task_type)
        if len(snapshots) < 2:  # type: ignore
            return None

        latest, previous = snapshots[-1], snapshots[-2]  # type: ignore

        def compute_delta(field: str) -> StatDelta:
            current = getattr(latest, field, 0)
            old = getattr(previous, field, 0)
            delta = current - old
            percentage = (delta / old * 100) if old else 0.0
            return StatDelta(value=current, change=delta, percentage=round(percentage, 2))

        return TaskStatSummary(
            task_type=task_type,
            imported=compute_delta("imported"),
            parsed=compute_delta("parsed"),
            trimmed=compute_delta("trimmed"),
            deduped=compute_delta("deduped"),
            total_playtime=compute_delta("total_playtime"),
            total_filesize=compute_delta("total_filesize"),
        )

    @strawberry.field
    async def get_tracks(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
    ) -> Paginated[Track]:  # type: ignore
        async for session in DBInstance.get_session():
            stmt = select(DBTrack).offset(offset).limit(limit)
            total_stmt = select(func.count()).select_from(DBTrack)

            results = await session.exec(stmt)
            total = await session.exec(total_stmt)
            total_count = total.one() if total else 0

            return Paginated[Track](items=[map_dbtrack_to_track(track) for track in results], total=total_count)

    @strawberry.field
    async def get_albums(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
    ) -> Paginated[Album]:  # type: ignore
        async for session in DBInstance.get_session():
            stmt = select(DBAlbum).offset(offset).limit(limit)
            total_stmt = select(func.count()).select_from(DBAlbum)

            results = await session.exec(stmt)
            total = await session.exec(total_stmt)
            total_count = total.one() if total else 0

            return Paginated[Album](items=[map_dbalbum_to_album(album) for album in results], total=total_count)

    @strawberry.field
    async def get_persons(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
    ) -> Paginated[Person]:  # type: ignore
        async for session in DBInstance.get_session():
            stmt = select(DBPerson).offset(offset).limit(limit)
            total_stmt = select(func.count()).select_from(DBPerson)

            results = await session.exec(stmt)
            total = await session.exec(total_stmt)
            total_count = total.one() if total else 0

            return Paginated[Person](items=[map_dbperson_to_person(person) for person in results], total=total_count)

    @strawberry.field
    async def get_labels(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
    ) -> Paginated[Label]:  # type: ignore
        async for session in DBInstance.get_session():
            stmt = select(DBLabel).offset(offset).limit(limit)
            total_stmt = select(func.count()).select_from(DBLabel)

            results = await session.exec(stmt)
            total = await session.exec(total_stmt)
            total_count = total.one() if total else 0

            return Paginated[Label](items=[map_dblabel_to_label(label) for label in results], total=total_count)

    @strawberry.field
    async def get_file(self, info: Info, file_id: int) -> FileType | None:
        """Retrieve a single file by ID."""
        async for session in DBInstance.get_session():
            return await session.get(DBFile, file_id)  # type: ignore

    @strawberry.field
    async def files(self, info: Info, limit: int = 20, offset: int = 0) -> list[FileType]:  # type: ignore
        """Paginated file listing."""
        async for session in DBInstance.get_session():
            result = await session.execute(select(DBFile).offset(offset).limit(limit))
            return result.scalars().all()  # type: ignore


@strawberry.field
async def get_user(self, info: Info, user_id: int) -> Optional[User]:
    """Fetch a single user by ID."""
    async for session in DBInstance.get_session():
        user = await session.get(DBUser, user_id)
        return map_dbuser_to_user(user) if user else None
