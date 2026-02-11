import aiohttp
import strawberry
from strawberry.types import Info
from sqlmodel import select

from Singletons import DBInstance
from config import Config
from auth.jwt_utils import create_access_token, create_refresh_token
from core.enums import UserRole
from core.dbmodels import (
    DBTrack,
    DBAlbum,
    DBPerson,
    DBGenre,
    DBFile,
    DBUser,
    DBLabel,
    DBPlaylist,
    DBPlaylistTrack,
    DBQueue,
)
from .playerservice import get_player_service
from .mapping import (
    update_model_from_input,
    map_dbuser_to_user,
    map_dbplaylist_to_playlist,
    map_dblabel_to_label,
)
from .schemas import (
    TrackInput,
    AlbumInput,
    PersonInput,
    GenreInput,
    FileInput,
    LabelInput,
    UserCreateInput,
    UserUpdateInput,
    User,
    Label,
    Playlist,
    Queue,
    AuthPayload,
)


def _require_user(info: Info) -> DBUser:
    user = getattr(info.context, "user", None)
    if user is None:
        raise ValueError("Authentication required")
    return user


def _is_admin(user: DBUser) -> bool:
    role = getattr(user, "role", None)
    if isinstance(role, UserRole):
        return role == UserRole.ADMIN
    if isinstance(role, str):
        normalized = role.strip().lower()
        return normalized in {UserRole.ADMIN.value.lower(), UserRole.ADMIN.name.lower()}
    return False


def _require_admin(info: Info) -> DBUser:
    user = _require_user(info)
    if not _is_admin(user):
        raise ValueError("Admin role required")
    return user


@strawberry.type
class Mutation:
    """GraphQL Mutations to update metadata or control playback."""

    @strawberry.mutation
    async def login_with_google(self, info: Info, id_token: str) -> AuthPayload:
        """
        Validate a Google ID token and return AMM access/refresh tokens.
        Enforces username whitelist and admin username from config.
        """
        config = Config.get_sync()
        client_id = config.get_string("auth", "google_client_id", "")
        if not client_id:
            raise ValueError("Google client ID not configured")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
            ) as resp:
                if resp.status != 200:
                    raise ValueError("Invalid Google token")
                token_info = await resp.json()

        if token_info.get("aud") != client_id:
            raise ValueError("Invalid token audience")

        email = token_info.get("email")
        if not email:
            raise ValueError("Google token missing email")

        username = email.split("@")[0]
        allowed = config.get_list("auth", "allowed_usernames", [])
        admin_usernames = config.get_list("auth", "admin_usernames", [])
        admin_set = {name for name in admin_usernames if name}

        if allowed and username not in allowed and username not in admin_set:
            raise ValueError("User not allowed")

        role = UserRole.ADMIN if username in admin_set else UserRole.USER

        async for db in DBInstance.get_session():
            result = await db.exec(select(DBUser).where(DBUser.email == email))
            user = result.first()

            if not user:
                user = DBUser(
                    username=username,
                    email=email,
                    first_name=token_info.get("given_name", "") or "",
                    last_name=token_info.get("family_name", "") or "",
                    role=role,
                    is_active=True,
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            else:
                if not user.is_active:
                    raise ValueError("Inactive user")
                if username in admin_set and user.role != UserRole.ADMIN:
                    user.role = UserRole.ADMIN
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)

        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        return AuthPayload(
            access_token=access_token,
            refresh_token=refresh_token,
            user=map_dbuser_to_user(user),
        )

    @strawberry.mutation
    async def create_user(self, info: Info, data: UserCreateInput) -> User:
        """Create a new user."""
        _require_admin(info)
        user = DBUser(
            username=data.username,
            email=str(data.email),
            password_hash=data.password_hash,
            first_name=data.first_name or "",
            middle_name=data.middle_name,
            last_name=data.last_name or "",
            is_active=True if data.is_active is None else data.is_active,
        )
        if data.role is not None:
            user.role = data.role
        async for session in DBInstance.get_session():
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return map_dbuser_to_user(user)

    @strawberry.mutation
    async def update_user(self, info: Info, user_id: int, data: UserUpdateInput) -> User:
        """Update an existing user."""
        _require_admin(info)
        async for session in DBInstance.get_session():
            user = await session.get(DBUser, user_id)
            if not user:
                raise ValueError("User not found")
            update_model_from_input(user, data)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return map_dbuser_to_user(user)

        raise ValueError("User update failed")

    @strawberry.mutation
    async def delete_user(self, info: Info, user_id: int) -> User:
        """Delete a user."""
        _require_admin(info)
        async for session in DBInstance.get_session():
            user = await session.get(DBUser, user_id)
            if not user:
                raise ValueError("User not found")
            await session.delete(user)
            await session.commit()
            return map_dbuser_to_user(user)

        raise ValueError("User deletion failed")

    @strawberry.mutation
    async def update_track(self, info: Info, track_id: int, data: TrackInput) -> bool:
        """Update an existing track using provided input fields."""
        async for session in DBInstance.get_session():
            track = await session.get(DBTrack, track_id)
            if track:
                update_model_from_input(track, data)
                session.add(track)
                await session.commit()
                return True
        return False

    @strawberry.mutation
    async def update_album(self, info: Info, album_id: int, data: AlbumInput) -> bool:
        """Update an existing album."""
        async for session in DBInstance.get_session():
            album = await session.get(DBAlbum, album_id)
            if album:
                update_model_from_input(album, data)
                session.add(album)
                await session.commit()
                return True
        return False

    @strawberry.mutation
    async def update_person(self, info: Info, person_id: int, data: PersonInput) -> bool:
        """Update an existing person (artist, performer, etc)."""
        async for session in DBInstance.get_session():
            person = await session.get(DBPerson, person_id)
            if person:
                update_model_from_input(person, data)
                session.add(person)
                await session.commit()
                return True
        return False

    @strawberry.mutation
    async def update_genre(self, info: Info, genre_id: int, data: GenreInput) -> bool:
        """Update an existing genre."""
        async for session in DBInstance.get_session():
            genre = await session.get(DBGenre, genre_id)
            if genre:
                update_model_from_input(genre, data)
                session.add(genre)
                await session.commit()
                return True
        return False

    @strawberry.mutation
    async def update_label(self, info: Info, label_id: int, data: LabelInput) -> Label:
        """Update an existing label."""
        async for session in DBInstance.get_session():
            label = await session.get(DBLabel, label_id)
            if not label:
                raise ValueError("Label not found")
            update_model_from_input(label, data)
            session.add(label)
            await session.commit()
            await session.refresh(label)
            return map_dblabel_to_label(label)

        raise ValueError("Label update failed")

    @strawberry.mutation
    async def create_playlist(self, info: Info, name: str) -> Playlist:
        """Create a new playlist for the current user."""
        user = _require_user(info)
        playlist = DBPlaylist(name=name, user_id=user.id)
        async for session in DBInstance.get_session():
            session.add(playlist)
            await session.commit()
            await session.refresh(playlist)
            return map_dbplaylist_to_playlist(playlist)

        raise ValueError("Playlist creation failed")

    @strawberry.mutation
    async def rename_playlist(self, info: Info, playlist_id: int, name: str) -> Playlist:
        """Rename an existing playlist."""
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(
                select(DBPlaylist).where(DBPlaylist.id == playlist_id).where(DBPlaylist.user_id == user.id)
            )
            playlist = result.first()
            if not playlist:
                raise ValueError("Playlist not found")
            playlist.name = name
            session.add(playlist)
            await session.commit()
            await session.refresh(playlist)
            return map_dbplaylist_to_playlist(playlist)

        raise ValueError("Playlist rename failed")

    @strawberry.mutation
    async def delete_playlist(self, info: Info, playlist_id: int) -> bool:
        """Delete a playlist."""
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(
                select(DBPlaylist).where(DBPlaylist.id == playlist_id).where(DBPlaylist.user_id == user.id)
            )
            playlist = result.first()
            if not playlist:
                return False
            await session.delete(playlist)
            await session.commit()
            return True

        return False

    @strawberry.mutation
    async def add_track_to_playlist(
        self,
        info: Info,
        playlist_id: int,
        track_id: int,
        position: int | None = None,
    ) -> Playlist:
        """Add a track to a playlist."""
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(
                select(DBPlaylist).where(DBPlaylist.id == playlist_id).where(DBPlaylist.user_id == user.id)
            )
            playlist = result.first()
            if not playlist:
                raise ValueError("Playlist not found")

            current_positions = [t.position for t in playlist.tracks]
            next_pos = (max(current_positions) + 1) if current_positions else 0
            pos = next_pos if position is None else position
            link = DBPlaylistTrack(playlist_id=playlist.id, track_id=track_id, position=pos)
            session.add(link)
            await session.commit()
            await session.refresh(playlist)
            return map_dbplaylist_to_playlist(playlist)

        raise ValueError("Playlist update failed")

    @strawberry.mutation
    async def remove_track_from_playlist(
        self,
        info: Info,
        playlist_id: int,
        track_id: int,
    ) -> Playlist:
        """Remove a track from a playlist."""
        user = _require_user(info)
        async for session in DBInstance.get_session():
            playlist_result = await session.exec(
                select(DBPlaylist).where(DBPlaylist.id == playlist_id).where(DBPlaylist.user_id == user.id)
            )
            playlist = playlist_result.first()
            if not playlist:
                raise ValueError("Playlist not found")

            link_result = await session.exec(
                select(DBPlaylistTrack)
                .where(DBPlaylistTrack.playlist_id == playlist_id)
                .where(DBPlaylistTrack.track_id == track_id)
            )
            link = link_result.first()
            if link:
                await session.delete(link)
                await session.commit()
            await session.refresh(playlist)
            return map_dbplaylist_to_playlist(playlist)

        raise ValueError("Playlist update failed")

    @strawberry.mutation
    async def set_playlist_tracks(self, info: Info, playlist_id: int, track_ids: list[int]) -> Playlist:
        """Replace the full track list for a playlist."""
        user = _require_user(info)
        async for session in DBInstance.get_session():
            playlist_result = await session.exec(
                select(DBPlaylist).where(DBPlaylist.id == playlist_id).where(DBPlaylist.user_id == user.id)
            )
            playlist = playlist_result.first()
            if not playlist:
                raise ValueError("Playlist not found")

            # delete existing tracks
            for link in list(playlist.tracks):
                await session.delete(link)

            # add new tracks with order
            for idx, track_id in enumerate(track_ids):
                session.add(DBPlaylistTrack(playlist_id=playlist.id, track_id=track_id, position=idx))

            await session.commit()
            await session.refresh(playlist)
            return map_dbplaylist_to_playlist(playlist)

        raise ValueError("Playlist update failed")

    @strawberry.mutation
    async def queue_track(self, info: Info, track_id: int) -> bool:
        """Queue a track for the current user."""
        user = _require_user(info)
        player = await get_player_service(user.id)
        await player.queue_track(track_id)
        return True

    @strawberry.mutation
    async def set_queue(self, info: Info, track_ids: list[int]) -> Queue:
        """Replace the entire queue for the current user."""
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(select(DBQueue).where(DBQueue.user_id == user.id))
            queue = result.first()
            if queue:
                queue.track_ids = track_ids
                session.add(queue)
            else:
                queue = DBQueue(user_id=user.id, track_ids=track_ids)
                session.add(queue)
            await session.commit()
            player = await get_player_service(user.id)
            player.queue = list(queue.track_ids)
            return Queue(track_ids=queue.track_ids)

        raise ValueError("Queue update failed")

    @strawberry.mutation
    async def clear_queue(self, info: Info) -> Queue:
        """Clear the current user's queue."""
        return await self.set_queue(info, [])

    @strawberry.mutation
    async def remove_from_queue(self, info: Info, track_id: int) -> Queue:
        """Remove the first instance of a track from the queue."""
        user = _require_user(info)
        async for session in DBInstance.get_session():
            result = await session.exec(select(DBQueue).where(DBQueue.user_id == user.id))
            queue = result.first()
            if not queue:
                return Queue(track_ids=[])
            if track_id in queue.track_ids:
                queue.track_ids.remove(track_id)
                session.add(queue)
                await session.commit()
                player = await get_player_service(user.id)
                player.queue = list(queue.track_ids)
            return Queue(track_ids=queue.track_ids)

        raise ValueError("Queue update failed")

    @strawberry.mutation
    async def play_next(self, info: Info) -> bool:
        """Play the next track in the queue."""
        user = _require_user(info)
        player = await get_player_service(user.id)
        await player.play_next()
        return True

    @strawberry.mutation
    async def pause(self, info: Info) -> bool:
        """Pause playback (stops Icecast stream)."""
        user = _require_user(info)
        player = await get_player_service(user.id)
        await player.pause()
        return True

    @strawberry.mutation
    async def stop(self, info: Info) -> bool:
        """Stop playback completely."""
        user = _require_user(info)
        player = await get_player_service(user.id)
        await player.stop()
        return True

    @strawberry.mutation
    async def set_position(self, info: Info, seconds: int) -> bool:
        user = _require_user(info)
        player = await get_player_service(user.id)
        await player.seek(seconds)
        return True

    @strawberry.mutation
    async def update_file(self, info: Info, file_id: int, data: FileInput) -> bool:
        """Update file metadata (path, size, format, etc)."""
        async for session in DBInstance.get_session():
            file = await session.get(DBFile, file_id)
            if file:
                update_model_from_input(file, data)
                session.add(file)
                await session.commit()
                return True
        return False

    @strawberry.mutation
    async def delete_file(self, info: Info, file_id: int) -> bool:
        """Delete a file entry completely."""
        async for session in DBInstance.get_session():
            file = await session.get(DBFile, file_id)
            if file:
                await session.delete(file)
                await session.commit()
                return True
        return False

    @strawberry.mutation
    async def start_export(self, info: Info) -> bool:
        """Placeholder for future export task."""
        return False
