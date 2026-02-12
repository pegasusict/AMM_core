import strawberry
from strawberry.types import Info
from sqlmodel import select

from Singletons import DBInstance
from auth.jwt_utils import create_access_token, create_refresh_token
from auth.passwords import hash_password, verify_password
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
    async def login(self, info: Info, username_or_email: str, password: str) -> AuthPayload:
        """Local username/email + password login."""
        username_or_email = (username_or_email or "").strip()
        if not username_or_email:
            raise ValueError("Username or email is required")
        if not password:
            raise ValueError("Password is required")

        async for session in DBInstance.get_session():
            stmt = select(DBUser).where(
                (DBUser.username == username_or_email) | (DBUser.email == username_or_email)
            )
            user = (await session.exec(stmt)).first()
            if not user or not user.is_active:
                raise ValueError("Invalid username/email or password")
            if not verify_password(password, user.password_hash):
                raise ValueError("Invalid username/email or password")

            access_token = create_access_token({"sub": str(user.id), "email": str(user.email)})
            refresh_token = create_refresh_token({"sub": str(user.id)})
            return AuthPayload(
                access_token=access_token,
                refresh_token=refresh_token,
                user=map_dbuser_to_user(user),
            )

        raise ValueError("Login failed")

    @strawberry.mutation
    async def refresh_session(self, info: Info, refresh_token: str) -> AuthPayload:
        """Exchange a refresh token for a new session."""
        refresh_token = (refresh_token or "").strip()
        if not refresh_token:
            raise ValueError("Refresh token is required")

        from jose import jwt, JWTError
        from auth.jwt_utils import SECRET_KEY, ALGORITHM

        try:
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError as exc:
            raise ValueError("Invalid refresh token") from exc

        token_type = payload.get("type")
        if token_type is not None and str(token_type) != "refresh":
            raise ValueError("Invalid refresh token")

        sub = payload.get("sub")
        if not sub:
            raise ValueError("Invalid refresh token")
        user_id = int(sub)

        async for session in DBInstance.get_session():
            user = await session.get(DBUser, user_id)
            if not user or not user.is_active:
                raise ValueError("Inactive user")
            access_token = create_access_token({"sub": str(user.id), "email": str(user.email)})
            new_refresh = create_refresh_token({"sub": str(user.id)})
            return AuthPayload(
                access_token=access_token,
                refresh_token=new_refresh,
                user=map_dbuser_to_user(user),
            )

    @strawberry.mutation
    async def create_user(self, info: Info, data: UserCreateInput) -> User:
        """Create a new user."""
        _require_admin(info)
        password_hash = hash_password(data.password)
        user = DBUser(
            username=data.username,
            email=str(data.email),
            password_hash=password_hash,
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
            # Handle password explicitly so we never accept a raw hash from clients.
            if getattr(data, "password", None) is not None:
                user.password_hash = hash_password(getattr(data, "password"))  # type: ignore[arg-type]
                # Prevent generic mapping from clobbering password_hash.
                setattr(data, "password", None)
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
