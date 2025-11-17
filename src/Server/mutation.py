import strawberry
from strawberry.types import Info

from Singletons import DBInstance
from dbmodels import (
    DBTrack,
    DBAlbum,
    DBPerson,
    DBGenre,
    DBFile,
)
from playerservice import get_player_service
from mapping import update_model_from_input
from schemas import (
    TrackInput,
    AlbumInput,
    PersonInput,
    GenreInput,
    FileInput,
)


@strawberry.type
class Mutation:
    """GraphQL Mutations to update metadata or control playback."""

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
    async def queue_track(self, info: Info, track_id: int) -> bool:
        """Queue a track for the current user."""
        user = info.context["user"]
        player = await get_player_service(user.id)
        await player.queue_track(track_id)
        return True

    @strawberry.mutation
    async def play_next(self, info: Info) -> bool:
        """Play the next track in the queue."""
        user = info.context["user"]
        player = await get_player_service(user.id)
        await player.play_next()
        return True

    @strawberry.mutation
    async def pause(self, info: Info) -> bool:
        """Pause playback (stops Icecast stream)."""
        user = info.context["user"]
        player = await get_player_service(user.id)
        await player.pause()
        return True

    @strawberry.mutation
    async def stop(self, info: Info) -> bool:
        """Stop playback completely."""
        user = info.context["user"]
        player = await get_player_service(user.id)
        await player.stop()
        return True

    @strawberry.mutation
    async def set_volume(self, info: Info, level: int) -> bool:
        user = info.context["user"]
        player = await get_player_service(user.id)
        await player.set_volume(level)
        return True

    @strawberry.mutation
    async def save_volume(self, info: Info, level: int) -> bool:
        user = info.context["user"]
        async for session in DBInstance.get_session():
            user.volume = level
            session.add(user)
            await session.commit()
        return True

    @strawberry.mutation
    async def set_position(self, info: Info, seconds: int) -> bool:
        user = info.context["user"]
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
