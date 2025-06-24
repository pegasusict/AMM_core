# -*- coding: utf-8 -*-
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
GraphQL Server class for handling GraphQL queries and mutations.
This class is used to add a GraphQL route to the FastAPI application.
"""

import asyncio
import strawberry
from strawberry.types import Info
from typing import Optional

from ..dbmodels import (
    DBTrack,
    DBAlbum,
    DBPerson,
    DBGenre,
    # DBUser,
    # DBPlaylist,
    # DBPlaylistTrack,
    # DBQueue,
)
from ..Singletons.database import DBInstance
from .schemas import (
    Track,
    Album,
    Person,
    Genre,
    # Playlist,
    # PlayerStatus,
    PlayerTrack,
    TrackInput,
    AlbumInput,
    PersonInput,
    GenreInput,
)
from .playerservice import get_player_service
from .mapping import (
    map_dbtrack_to_track,
    map_dbalbum_to_album,
    map_dbperson_to_person,
    map_dbgenre_to_genre,
    # map_dbplaylist_to_playlist,
    map_dbtrack_to_playertrack,
    update_model_from_input,
)


# ------------------ GraphQL Queries ------------------


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


# ------------------ GraphQL Mutations ------------------


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
    async def update_person(
        self, info: Info, person_id: int, data: PersonInput
    ) -> bool:
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


# ------------------ GraphQL Subscriptions ------------------


@strawberry.type
class Subscription:
    """GraphQL Subscription to notify when track changes."""

    @strawberry.subscription
    async def track_changed(self, info: Info) -> PlayerTrack:  # type: ignore
        """
        Subscription that notifies when the next track starts playing
        for the current user.
        """
        user = info.context["user"]
        player = await get_player_service(user.id)
        while True:
            await asyncio.sleep(1)  # Polling interval
            if player.queue:
                async for session in DBInstance.get_session():
                    track = await session.get(DBTrack, player.queue[0])
                    if track:
                        yield map_dbtrack_to_playertrack(track)  # type: ignore


# ------------------ GraphQL Schema ------------------

schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
