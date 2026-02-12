from typing import Optional, TypeVar, Any

import strawberry
from strawberry.types import Info
from sqlmodel import func, select
from sqlalchemy import or_

from Enums import TaskType, UserRole
from core.dbmodels import (
    DBTask,
    DBTrack,
    DBAlbum,
    DBPerson,
    DBGenre,
    DBLabel,
    DBFile,
    DBUser,
    DBPlaylist,
    DBQueue,
    DBStat,
    DBTaskStatSnapshot,
    DBAlbumTrack,
    DBTrackTag,
    DBKey,
    DBTrackLyric,
    DBPicture,
    DBPlaylistTrack,
)
from core.registry import registry
from core.taskmanager import TaskManager
from Singletons.database import DBInstance
from .schemas import (
    DisplayTask,
    Paginated,
    StatDelta,
    StatPoint,
    TaskStatSummary,
    TaskStatTrend,
    TaskStats,
    TaskStatSnapshot,
    Task,
    Stat,
    File,
    Track,
    Album,
    Person,
    Genre,
    Label,
    User,
    Playlist,
    Queue,
    AlbumTrack,
    TrackTag,
    Key,
    TrackLyric,
    Picture,
    PlaylistTrack,
)
from .mapping import (
    map_dbtask_to_displaytask,
    map_dbtask_to_task,
    map_dbtrack_to_track,
    map_dbalbum_to_album,
    map_dbperson_to_person,
    map_dbgenre_to_genre,
    map_dblabel_to_label,
    map_dbuser_to_user,
    map_dbfile_to_file,
    map_dbplaylist_to_playlist,
    map_dbqueue_to_queue,
    map_dbstat_to_stat,
    map_dbalbum_track_to_album_track,
    map_dbtrack_tag_to_track_tag,
    map_dbkey_to_key,
    map_dbtrack_lyric_to_track_lyric,
    map_dbpicture_to_picture,
    map_dbplaylist_track_to_playlist_track,
)


def _require_user(info: Info) -> DBUser:
    user = getattr(info.context, "user", None)
    if user is None:
        raise ValueError("Authentication required")
    return user


TModel = TypeVar("TModel")
TGraph = TypeVar("TGraph")


async def _paginate(
    model: type[TModel],
    mapper: Any,
    limit: int,
    offset: int,
) -> Paginated[TGraph]:  # type: ignore
    async for session in DBInstance.get_session():
        stmt = select(model).offset(offset).limit(limit)
        total_stmt = select(func.count()).select_from(model)

        results = await session.exec(stmt)
        total = await session.exec(total_stmt)
        total_count = total.one() if total else 0
        items = results.all()

        return Paginated[TGraph](items=[mapper(item) for item in items], total=total_count)


@strawberry.type
class Query:
    """GraphQL Queries."""

    @strawberry.field
    async def get_task(self, info: Info, task_id: int) -> Optional[Task]:
        async for session in DBInstance.get_session():
            task = await session.get(DBTask, task_id)
            return map_dbtask_to_task(task) if task else None

    @strawberry.field
    async def tasks(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Task]:  # type: ignore
        return await _paginate(DBTask, map_dbtask_to_task, limit, offset)

    @strawberry.field
    async def get_task_display(self, info: Info) -> Optional[list[DisplayTask]]:
        async for session in DBInstance.get_session():
            result = await session.exec(select(DBTask))
            tasks = result.all()
            return [map_dbtask_to_displaytask(task) for task in tasks] if tasks else []

    @strawberry.field
    async def task_stats(self, info: Info, task_type: TaskType) -> Optional[TaskStats]:
        stat = await DBInstance.get_task_stats(task_type)
        return TaskStats(**stat.dict()) if stat else None

    @strawberry.field
    async def task_stat_snapshots(
        self,
        info: Info,
        task_type: TaskType,
        limit: int = 25,
        offset: int = 0,
    ) -> Paginated[TaskStatSnapshot]:  # type: ignore
        async for session in DBInstance.get_session():
            stmt = (
                select(DBTaskStatSnapshot)
                .where(DBTaskStatSnapshot.task_type == task_type)
                .order_by(DBTaskStatSnapshot.snapshot_time)  # type: ignore
                .offset(offset)
                .limit(limit)
            )
            total_stmt = select(func.count()).select_from(DBTaskStatSnapshot).where(DBTaskStatSnapshot.task_type == task_type)

            results = await session.exec(stmt)
            total = await session.exec(total_stmt)
            total_count = total.one() if total else 0
            snaps = results.all()
            mapped = [TaskStatSnapshot(**snap.dict()) for snap in snaps]
            return Paginated[TaskStatSnapshot](items=mapped, total=total_count)

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
    async def get_stat(self, info: Info, stat_id: int) -> Optional[Stat]:
        async for session in DBInstance.get_session():
            stat = await session.get(DBStat, stat_id)
            return map_dbstat_to_stat(stat) if stat else None

    @strawberry.field
    async def stats(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Stat]:  # type: ignore
        return await _paginate(DBStat, map_dbstat_to_stat, limit, offset)

    @strawberry.field
    async def get_track(self, info: Info, track_id: int) -> Optional[Track]:
        async for session in DBInstance.get_session():
            track = await session.get(DBTrack, track_id)
            return map_dbtrack_to_track(track) if track else None

    @strawberry.field
    async def tracks(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Track]:  # type: ignore
        return await _paginate(DBTrack, map_dbtrack_to_track, limit, offset)

    @strawberry.field
    async def get_tracks(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Track]:  # type: ignore
        return await _paginate(DBTrack, map_dbtrack_to_track, limit, offset)

    @strawberry.field
    async def get_album(self, info: Info, album_id: int) -> Optional[Album]:
        async for session in DBInstance.get_session():
            album = await session.get(DBAlbum, album_id)
            return map_dbalbum_to_album(album) if album else None

    @strawberry.field
    async def albums(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Album]:  # type: ignore
        return await _paginate(DBAlbum, map_dbalbum_to_album, limit, offset)

    @strawberry.field
    async def get_albums(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Album]:  # type: ignore
        return await _paginate(DBAlbum, map_dbalbum_to_album, limit, offset)

    @strawberry.field
    async def get_person(self, info: Info, person_id: int) -> Optional[Person]:
        async for session in DBInstance.get_session():
            person = await session.get(DBPerson, person_id)
            return map_dbperson_to_person(person) if person else None

    @strawberry.field
    async def persons(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Person]:  # type: ignore
        return await _paginate(DBPerson, map_dbperson_to_person, limit, offset)

    @strawberry.field
    async def get_persons(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Person]:  # type: ignore
        return await _paginate(DBPerson, map_dbperson_to_person, limit, offset)

    @strawberry.field
    async def get_genre(self, info: Info, genre_id: int) -> Optional[Genre]:
        async for session in DBInstance.get_session():
            genre = await session.get(DBGenre, genre_id)
            return map_dbgenre_to_genre(genre) if genre else None

    @strawberry.field
    async def genres(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Genre]:  # type: ignore
        return await _paginate(DBGenre, map_dbgenre_to_genre, limit, offset)

    @strawberry.field
    async def get_label(self, info: Info, label_id: int) -> Optional[Label]:
        async for session in DBInstance.get_session():
            label = await session.get(DBLabel, label_id)
            return map_dblabel_to_label(label) if label else None

    @strawberry.field
    async def labels(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Label]:  # type: ignore
        return await _paginate(DBLabel, map_dblabel_to_label, limit, offset)

    @strawberry.field
    async def get_labels(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Label]:  # type: ignore
        return await _paginate(DBLabel, map_dblabel_to_label, limit, offset)

    @strawberry.field
    async def get_file(self, info: Info, file_id: int) -> Optional[File]:
        async for session in DBInstance.get_session():
            file = await session.get(DBFile, file_id)
            return map_dbfile_to_file(file) if file else None

    @strawberry.field
    async def files(self, info: Info, limit: int = 20, offset: int = 0) -> list[File]:  # type: ignore
        async for session in DBInstance.get_session():
            result = await session.exec(select(DBFile).offset(offset).limit(limit))
            files = result.all()
            return [map_dbfile_to_file(file) for file in files] if files else []

    @strawberry.field
    async def get_user(self, info: Info, user_id: int) -> Optional[User]:
        async for session in DBInstance.get_session():
            user = await session.get(DBUser, user_id)
            return map_dbuser_to_user(user) if user else None

    @strawberry.field
    async def me(self, info: Info) -> Optional[User]:
        user = _require_user(info)
        return map_dbuser_to_user(user)

    @strawberry.field
    async def users(
        self,
        info: Info,
        limit: int = 25,
        offset: int = 0,
        username: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Paginated[User]:  # type: ignore
        stmt = select(DBUser)
        filters = []
        if username:
            filters.append(DBUser.username == username)
        if email:
            filters.append(DBUser.email == email)
        if role:
            filters.append(DBUser.role == role.value)
        if is_active is not None:
            filters.append(DBUser.is_active == is_active)
        if search:
            like = f"%{search}%"
            filters.append(
                or_(
                    DBUser.username.ilike(like),
                    DBUser.email.ilike(like),
                    DBUser.first_name.ilike(like),
                    DBUser.last_name.ilike(like),
                )
            )
        for f in filters:
            stmt = stmt.where(f)

        async for session in DBInstance.get_session():
            total_stmt = select(func.count()).select_from(DBUser)
            for f in filters:
                total_stmt = total_stmt.where(f)
            total = await session.exec(total_stmt)
            total_count = total.one() if total else 0

            results = await session.exec(stmt.offset(offset).limit(limit))
            users = results.all()
            return Paginated[User](items=[map_dbuser_to_user(u) for u in users], total=total_count)

    @strawberry.field
    async def get_album_track(self, info: Info, album_track_id: int) -> Optional[AlbumTrack]:
        async for session in DBInstance.get_session():
            album_track = await session.get(DBAlbumTrack, album_track_id)
            return map_dbalbum_track_to_album_track(album_track) if album_track else None

    @strawberry.field
    async def album_tracks(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[AlbumTrack]:  # type: ignore
        return await _paginate(DBAlbumTrack, map_dbalbum_track_to_album_track, limit, offset)

    @strawberry.field
    async def get_track_tag(self, info: Info, track_tag_id: int) -> Optional[TrackTag]:
        async for session in DBInstance.get_session():
            track_tag = await session.get(DBTrackTag, track_tag_id)
            return map_dbtrack_tag_to_track_tag(track_tag) if track_tag else None

    @strawberry.field
    async def track_tags(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[TrackTag]:  # type: ignore
        return await _paginate(DBTrackTag, map_dbtrack_tag_to_track_tag, limit, offset)

    @strawberry.field
    async def get_key(self, info: Info, key_id: int) -> Optional[Key]:
        async for session in DBInstance.get_session():
            key = await session.get(DBKey, key_id)
            return map_dbkey_to_key(key) if key else None

    @strawberry.field
    async def keys(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Key]:  # type: ignore
        return await _paginate(DBKey, map_dbkey_to_key, limit, offset)

    @strawberry.field
    async def get_track_lyric(self, info: Info, track_lyric_id: int) -> Optional[TrackLyric]:
        async for session in DBInstance.get_session():
            track_lyric = await session.get(DBTrackLyric, track_lyric_id)
            return map_dbtrack_lyric_to_track_lyric(track_lyric) if track_lyric else None

    @strawberry.field
    async def track_lyrics(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[TrackLyric]:  # type: ignore
        return await _paginate(DBTrackLyric, map_dbtrack_lyric_to_track_lyric, limit, offset)

    @strawberry.field
    async def get_picture(self, info: Info, picture_id: int) -> Optional[Picture]:
        async for session in DBInstance.get_session():
            picture = await session.get(DBPicture, picture_id)
            return map_dbpicture_to_picture(picture) if picture else None

    @strawberry.field
    async def pictures(self, info: Info, limit: int = 25, offset: int = 0) -> Paginated[Picture]:  # type: ignore
        return await _paginate(DBPicture, map_dbpicture_to_picture, limit, offset)

    @strawberry.field
    async def get_playlist(self, info: Info, playlist_id: int) -> Optional[Playlist]:
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(
                select(DBPlaylist).where(DBPlaylist.id == playlist_id).where(DBPlaylist.user_id == user.id)
            )
            playlist = result.first()
            return map_dbplaylist_to_playlist(playlist) if playlist else None

    @strawberry.field
    async def playlist(self, info: Info, playlist_id: int) -> Optional[Playlist]:
        return await self.get_playlist(info, playlist_id)

    @strawberry.field
    async def playlists(self, info: Info) -> list[Playlist]:
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(select(DBPlaylist).where(DBPlaylist.user_id == user.id))
            playlists = result.all()
            return [map_dbplaylist_to_playlist(p) for p in playlists] if playlists else []

    @strawberry.field
    async def get_playlist_track(self, info: Info, playlist_track_id: int) -> Optional[PlaylistTrack]:
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(
                select(DBPlaylistTrack)
                .join(DBPlaylist, DBPlaylistTrack.playlist_id == DBPlaylist.id)
                .where(DBPlaylistTrack.id == playlist_track_id)
                .where(DBPlaylist.user_id == user.id)
            )
            playlist_track = result.first()
            return map_dbplaylist_track_to_playlist_track(playlist_track) if playlist_track else None

    @strawberry.field
    async def playlist_tracks(self, info: Info, playlist_id: int) -> list[PlaylistTrack]:
        user = _require_user(info)
        async for session in DBInstance.get_session():
            owner_result = await session.exec(
                select(DBPlaylist).where(DBPlaylist.id == playlist_id).where(DBPlaylist.user_id == user.id)
            )
            playlist = owner_result.first()
            if not playlist:
                return []

            result = await session.exec(select(DBPlaylistTrack).where(DBPlaylistTrack.playlist_id == playlist_id))
            links = result.all()
            ordered = sorted(links, key=lambda t: t.position)
            return [map_dbplaylist_track_to_playlist_track(link) for link in ordered]

    @strawberry.field
    async def queue(self, info: Info) -> Queue:
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(select(DBQueue).where(DBQueue.user_id == user.id))
            queue = result.first()
            return map_dbqueue_to_queue(queue)

    @strawberry.field
    async def get_queue(self, info: Info, queue_id: int) -> Optional[Queue]:
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(select(DBQueue).where(DBQueue.id == queue_id).where(DBQueue.user_id == user.id))
            queue = result.first()
            return map_dbqueue_to_queue(queue) if queue else None

    @strawberry.field
    async def start_import(self, info: Info) -> bool:
        tm = TaskManager()
        task_cls = registry.get_task_class("importer")
        if task_cls is None:
            return False
        await tm.start_task(task_cls)
        return True
