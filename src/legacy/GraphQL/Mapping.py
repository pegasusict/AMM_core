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
"""Module to define mappings between schemas and queries."""

from __future__ import annotations

from typing import Any, Mapping

import strawberry
from sqlmodel import select

from core.registry import registry
from core.taskmanager import TaskManager
from core.enums import TaskType
from Singletons import DBInstance
from Schemas import Track, Album, User, Person, Label, Stat, File, Genre
from dbmodels import DBAlbum, DBFile, DBGenre, DBLabel, DBPerson, DBTrack, DBUser, DBStat
from Exceptions import InvalidValueError

#################################################################################


def set_fields(info: Mapping[str, Any], subject: object) -> object:
    """Sets al non-empty values to the object."""
    for key, value in info.items():
        if key == "id":
            continue
        if value is not None:
            if hasattr(subject, key):
                setattr(subject, key, value)
    return subject


#################################################################################
async def _fetch_one(statement: Any) -> Any:
    async for session in DBInstance.get_session():
        result = await session.exec(statement)
        obj = result.first()
        await session.close()
        return obj
    return None


async def _update_db(info: Mapping[str, Any], statement: Any) -> Any:
    if not info:
        raise ValueError("No information provided to update the object")
    if "id" in info:
        raise ValueError("Cannot update ID directly")

    async for session in DBInstance.get_session():
        result = await session.exec(statement)
        obj = result.first()
        if obj is None:
            raise ValueError("Object not found")

        obj = set_fields(info, obj)
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        await session.close()
        return obj
    return None


async def resolve_user(info: Mapping[str, str | int]) -> User:
    """Logic to resolve a user via ID, username or email."""
    statement = select(DBUser)

    if (user_id := info.get("user_id", None)) is not None:
        statement = statement.where(DBUser.id == user_id)
    elif (username := info.get("username", None)) is not None:
        statement = statement.where(DBUser.username == username)
    elif (email := info.get("email", None)) is not None:
        statement = statement.where(DBUser.email == email)
    else:
        raise InvalidValueError("Invalid arguments for user resolution")

    user = await _fetch_one(statement)
    if user is None:
        raise InvalidValueError("User not found")

    user_obj = User()
    user_obj.__dict__.update(user.__dict__)

    return user_obj


async def resolve_track(info: Mapping[str, str | int], track_id: int | None = None) -> Track:
    """Logic to resolve a track by ID, MBid or title and artist."""
    statement = select(DBTrack)

    title = info.get("title", None)
    artist = info.get("artist", None)

    if track_id is not None:
        statement = statement.where(DBTrack.id == track_id)
    elif (mbid := info.get("mbid", None)) is not None:
        statement = statement.where(DBTrack.mbid == mbid)
    elif title is not None and artist is not None:
        statement = statement.where(DBTrack.title == title).where(artist in DBTrack.performers)
    else:
        raise ValueError("Invalid arguments for track resolution")

    track = await _fetch_one(statement)
    if track is None:
        raise InvalidValueError("Track not found")

    track_obj = Track()
    track_obj.__dict__.update(track.__dict__)

    return track_obj


async def resolve_album(info: Mapping[str, Any], album_id: int) -> Album:
    """Logic to resolve an album by ID, MBid, title and artist or release date."""
    statement = select(DBAlbum)

    title = info.get("title", None)
    artist = info.get("artist", None)

    if album_id is not None:
        statement = statement.where(DBAlbum.id == album_id)
    elif (mbid := info.get("mbid", None)) is not None:
        statement = statement.where(DBAlbum.mbid == mbid)
    elif title is not None and artist is not None:
        statement = statement.where(DBAlbum.title == title).where(artist in DBAlbum.performers)
    elif (release_date := info.get("release_date", None)) is not None:
        statement = statement.where(DBAlbum.release_date == release_date)
    else:
        raise ValueError("Invalid arguments for album resolution")

    album = await _fetch_one(statement)
    if album is None:
        raise InvalidValueError("Album not found")

    album_obj = Album()
    album_obj.__dict__.update(album.__dict__)

    return album_obj


async def resolve_person(info: Mapping[str, Any], person_id: int) -> Person:
    """Logic to resolve a person by ID, MBid, name, nickname or birth date."""
    statement = select(DBPerson)

    if person_id is not None:
        statement = statement.where(DBPerson.id == person_id)
    elif (mbid := info.get("mbid", None)) is not None:
        statement = statement.where(DBPerson.mbid == mbid)
    elif (nickname := info.get("nickname", None)) is not None:
        statement = statement.where(DBPerson.nick_name == nickname)
    elif (birth_date := info.get("birth_date", None)) is not None:
        statement = statement.where(DBPerson.date_of_birth == birth_date)
    else:
        raise ValueError("Invalid arguments for person resolution")

    person = await _fetch_one(statement)
    if person is None:
        raise InvalidValueError("Person not found")

    person_obj = Person()
    person_obj.__dict__.update(person.__dict__)

    return person_obj


async def resolve_label(info: Mapping[str, Any], label_id: int) -> Label:
    """Logic to resolve a label by ID or name."""
    statement = select(DBLabel)

    if label_id is not None:
        statement = statement.where(DBLabel.id == label_id)
    elif (name := info.get("name", None)) is not None:
        statement = statement.where(DBLabel.name == name)
    else:
        raise ValueError("Invalid arguments for label resolution")

    label = await _fetch_one(statement)
    if label is None:
        raise InvalidValueError("Label not found")

    label_obj = Label()
    label_obj.__dict__.update(label.__dict__)

    return label_obj


async def resolve_stat(info: Mapping[str, Any], stat_id: int) -> Stat:
    """Logic to resolve a stat by ID or name."""
    statement = select(DBStat)

    if (stat_id := info.get("stat_id", None)) is not None:
        statement = statement.where(DBStat.id == stat_id)
    elif (stat_id := info.get("id", None)) is not None:
        statement = statement.where(DBStat.id == stat_id)
    elif (name := info.get("name", None)) is not None:
        statement = statement.where(DBStat.name == name)
    else:
        raise ValueError("Invalid arguments for stat resolution")

    stat = await _fetch_one(statement)

    if stat is None:
        raise ValueError("Stat not found")

    stat_obj = Stat()
    stat_obj.__dict__.update(stat.__dict__)

    return stat_obj


async def resolve_file(info: Mapping[str, Any], file_id: int) -> File:
    """Logic to resolve a file by ID or filename."""

    statement = select(DBFile)

    if file_id is not None:
        statement = statement.where(DBFile.id == file_id)
    elif (file_id := info.get("id", None)) is not None:
        statement = statement.where(DBFile.id == file_id)
    elif (file_id := info.get("file_id", None)) is not None:
        statement = statement.where(DBFile.id == file_id)
    elif (filename := info.get("filename", None)) is not None:
        statement = statement.where(DBFile.file_name == filename)
    else:
        raise ValueError("Invalid arguments for file resolution")

    file = await _fetch_one(statement)
    if file is None:
        raise InvalidValueError("File not found")

    file_obj = File()
    file_obj.__dict__.update(file.__dict__)

    return file_obj


async def resolve_genre(info: Mapping[str, Any], genre_id: int) -> Genre:
    """Logic to resolve a genre by ID or name."""
    statement = select(DBGenre)

    if genre_id is not None:
        statement = statement.where(DBGenre.id == genre_id)
    elif (genre_id := info.get("id", None)) is not None:
        statement = statement.where(DBGenre.id == genre_id)
    elif (genre_id := info.get("genre_id", None)) is not None:
        statement = statement.where(DBGenre.id == genre_id)
    elif (name := info.get("name", None)) is not None:
        statement = statement.where(DBGenre.genre == name)
    else:
        raise ValueError("Invalid arguments for stat resolution")

    genre = await _fetch_one(statement)
    if genre is None:
        raise InvalidValueError("Genre not found")

    genre_obj = Genre()
    genre_obj.__dict__.update(genre.__dict__)

    return genre_obj


#################################################################################


async def start_import() -> dict[str, bool]:
    """Starts the import process."""
    tm = TaskManager()
    task_cls = registry.get_task_class("importer")
    if task_cls is None:
        return {"status": False}
    await tm.start_task(task_cls, batch=None)
    return {"status": True}


@strawberry.type()
class Query:
    """Query class for GraphQL schema."""

    track = strawberry.field(resolve_track)  # type: ignore
    album = strawberry.field(resolve_album)  # type: ignore
    person = strawberry.field(resolve_person)  # type: ignore
    user = strawberry.field(resolve_user)  # type: ignore
    label = strawberry.field(resolve_label)  # type: ignore
    stat = strawberry.field(resolve_stat)  # type: ignore
    file = strawberry.field(resolve_file)  # type: ignore
    genre = strawberry.field(resolve_genre)  # type: ignore
    start_import = strawberry.field(start_import)  # type: ignore


@strawberry.type()
class Mutation:
    """Mutation class for GraphQL schema."""

    @strawberry.mutation()
    async def create_user(self, info: Mapping[str, Any]) -> User:
        """Logic used to create a new user."""

        username = info.get("username", None)
        email = info.get("email", None)
        password_hash = info.get("password_hash", None)

        if username is None or email is None or password_hash is None:
            raise ValueError("Insufficient data to create a new user")

        user = DBUser(username=username, password_hash=password_hash, email=email)

        async for session in DBInstance.get_session():
            session.add(user)
            await session.commit()
            await session.refresh(user)
            await session.close()

        user_obj = User()
        user_obj.__dict__.update(user.__dict__)

        return user_obj

    @strawberry.mutation()
    async def update_user(self, info: Mapping[str, Any], user_id: int) -> User:
        """Updates user information."""
        self._verify_update_args(info, user_id)
        if "email" in info and not isinstance(info["email"], str):
            raise ValueError("Email must be a string")
        if "username" in info and not isinstance(info["username"], str):
            raise ValueError("Username must be a string")

        statement = select(DBUser).where(DBUser.id == user_id)
        user = await _update_db(info, statement)

        user_obj = User()
        user_obj.__dict__.update(user.__dict__)

        return user_obj

    @strawberry.mutation()
    async def delete_user(self, user_id: int) -> User:
        """Deletes a user from the system."""
        if user_id is None:
            raise ValueError("User ID is required for deletion")
        if not isinstance(user_id, int):
            raise ValueError("User ID must be an integer")

        async for session in DBInstance.get_session():
            result = await session.exec(select(DBUser).where(DBUser.id == user_id))
            user = result.first()

            if user is None:
                raise ValueError("User not found")

            await session.delete(user)
            await session.commit()
            await session.close()

        user_obj = User()
        user_obj.__dict__.update(user.__dict__)

        return user_obj

    def _verify_update_args(self, info: Mapping[str, Any], track_id: int) -> None:
        """Verifies the arguments for updating a track."""
        if track_id is None:
            raise InvalidValueError("Track ID is required for updating track information")
        if not isinstance(track_id, int):
            raise InvalidValueError("Track ID must be an integer")
        if not info:
            raise InvalidValueError("No information provided to update track")
        if "id" in info:
            raise InvalidValueError("Cannot update track ID directly")

    async def _update_db(self, info: Mapping[str, Any], statement: object) -> object:
        return await _update_db(info, statement)

    @strawberry.mutation()
    async def update_track(self, info: Mapping[str, Any], track_id: int) -> Track:
        """Updates track information."""
        self._verify_update_args(info, track_id)

        statement = select(DBTrack).where(DBTrack.id == track_id)
        track = await _update_db(info, statement)
        if track is None:
            raise InvalidValueError("Track not found")

        track_obj = Track()
        track_obj.__dict__.update(track.__dict__)

        return track_obj

    @strawberry.mutation()
    async def update_album(self, info: Mapping[str, Any], album_id: int) -> Album:
        """Updates album information."""
        self._verify_update_args(info, album_id)

        statement = select(DBAlbum).where(DBAlbum.id == album_id)
        album = await _update_db(info, statement)
        if album is None:
            raise InvalidValueError("Album not found")

        album_obj = Album()
        album_obj.__dict__.update(album.__dict__)

        return album_obj

    @strawberry.mutation()
    async def update_person(self, info: Mapping[str, Any], person_id: int) -> Person:
        """Updates person information."""
        self._verify_update_args(info, person_id)

        statement = select(DBPerson).where(DBPerson.id == person_id)
        person = await _update_db(info, statement)
        if person is None:
            raise InvalidValueError("Person not found")

        person_obj = Person()
        person_obj.__dict__.update(person.__dict__)

        return person_obj

    @strawberry.mutation()
    async def update_label(self, info: Mapping[str, Any], label_id: int) -> Label:
        """Updates label information."""
        self._verify_update_args(info, label_id)

        statement = select(DBLabel).where(DBLabel.id == label_id)
        label = await _update_db(info, statement)

        label_obj = Label()
        label_obj.__dict__.update(label.__dict__)

        return label_obj

    @strawberry.mutation()
    async def update_file(self, info: Mapping[str, Any], file_id: int) -> File:
        """Updates file information."""
        self._verify_update_args(info, file_id)

        statement = select(DBFile).where(DBFile.id == file_id)
        file = await _update_db(info, statement)

        file_obj = File()
        file_obj.__dict__.update(file.__dict__)

        return file_obj

    @strawberry.mutation()
    async def update_genre(self, info: Mapping[str, Any], genre_id: int) -> Genre:
        """Updates genre information."""
        self._verify_update_args(info, genre_id)

        statement = select(DBGenre).where(DBGenre.id == genre_id)
        genre = await _update_db(info, statement)

        genre_obj = Genre()
        genre_obj.__dict__.update(genre.__dict__)

        return genre_obj
