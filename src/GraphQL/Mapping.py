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

import strawberry
from sqlmodel import select

from Singletons.database import DB
from Schemas import Track, Album, User, Person, Label, Stat, File, Genre
from models import DBAlbum, DBFile, DBGenre, DBLabel, DBPerson, DBTrack, DBUser, DBStat
from Exceptions import InvalidValueError

#################################################################################


def set_fields(info: dict, subject: object) -> object:
    """Sets al non-empty values to the object."""
    for key, value in info:
        if key == "id":
            continue
        if value is not None:
            if hasattr(subject, key):
                subject.key = value  # type: ignore
    return subject


#################################################################################
def resolve_user(self, info: dict[str, str | int]) -> User:
    """Logic to resolve a user via ID, username or email."""
    statement = select(DBUser)

    if user_id := info.get("user_id", None) is not None:
        statement = statement.where(DBUser.id == user_id)
    elif username := info.get("username", None) is not None:
        statement = statement.where(DBUser.username == username)
    elif email := info.get("email", None) is not None:
        statement = statement.where(DBUser.email == email)
    else:
        raise InvalidValueError("Invalid arguments for user resolution")

    session = DB().get_session()
    user = session.exec(statement).first()
    session.close()

    user_obj = User()
    user_obj.__dict__.update(user.__dict__)

    return user_obj


def resolve_track(
    self, info: dict[str, str | int], track_id: int | None = None
) -> Track:
    """Logic to resolve a track by ID, MBid or title and artist."""
    statement = select(DBTrack)

    # title = info.get("title", None)
    # artist = info.get("artist", None)
    # album_id = info.get("album_id", None)
    # track_no = info.get("track_no", None)

    if track_id is not None:
        statement = statement.where(DBTrack.id == track_id)
    elif mbid := info.get("mbid", None) is not None:
        statement = statement.where(DBTrack.mbid == mbid)
    # elif title is not None and artist is not None:
    #     statement = statement.where(DBTrack.title == title).where(DBTrack.artists == artist)
    # elif album_id is not None and track_no is not None:
    #     statement = statement.where(DBTrack.album_id == album_id).where(DBTrack.track_no == track_no)
    else:
        raise ValueError("Invalid arguments for track resolution")

    session = DB().get_session()
    track = session.exec(statement).first()
    session.close()

    track_obj = Track()
    track_obj.__dict__.update(track.__dict__)

    return track_obj


def resolve_album(self, info: dict, album_id: int) -> Album:
    """Logic to resolve an album by ID, MBid, title and artist or release date."""
    statement = select(DBAlbum)

    # title = info.get("title", None)
    # artist = info.get("artist", None)

    if album_id is not None:
        statement = statement.where(DBAlbum.id == album_id)
    elif mbid := info.get("mbid", None) is not None:
        statement = statement.where(DBAlbum.mbid == mbid)
    # elif title is not None and artist is not None:
    # statement = statement.where(DBAlbum.title == title).where(DBAlbum.artists == artist)
    elif release_date := info.get("release_date", None) is not None:
        statement = statement.where(DBAlbum.release_date == release_date)
    else:
        raise ValueError("Invalid arguments for album resolution")

    session = DB().get_session()
    album = session.exec(statement).first()
    session.close()

    album_obj = Album()
    album_obj.__dict__.update(album.__dict__)

    return album_obj


def resolve_person(self, info: dict, person_id: int) -> Person:
    """Logic to resolve a person by ID, MBid, name, nickname or birth date."""
    statement = select(DBPerson)

    if person_id is not None:
        statement = statement.where(DBPerson.id == person_id)
    elif mbid := info.get("mbid", None) is not None:
        statement = statement.where(DBPerson.mbid == mbid)
    # elif name := info.get("name", None) is not None:
    #     statement = statement.where(DBPerson.name == name)
    elif nickname := info.get("nickname", None) is not None:
        statement = statement.where(DBPerson.nickname == nickname)
    elif birth_date := info.get("birth_date", None) is not None:
        statement = statement.where(DBPerson.birth_date == birth_date)
    else:
        raise ValueError("Invalid arguments for person resolution")

    session = DB().get_session()

    person = session.exec(statement).first()
    session.close()

    person_obj = Person()
    person_obj.__dict__.update(person.__dict__)

    return person_obj


def resolve_label(self, info: dict, label_id: int) -> Label:
    """Logic to resolve a label by ID or name."""
    statement = select(DBLabel)

    if label_id is not None:
        statement = statement.where(DBLabel.id == label_id)
    elif name := info.get("name", None) is not None:
        statement = statement.where(DBLabel.name == name)
    else:
        raise ValueError("Invalid arguments for label resolution")

    session = DB().get_session()
    label = session.exec(statement).first()
    session.close()

    label_obj = Label()
    label_obj.__dict__.update(label.__dict__)

    return label_obj


def resolve_stat(self, info: dict, stat_id: int) -> Stat:
    """Logic to resolve a stat by ID or name."""
    statement = select(DBStat)

    if stat_id := info.get("stat_id", None) is not None:
        statement = statement.where(DBStat.id == stat_id)
    elif stat_id := info.get("id", None) is not None:
        statement = statement.where(DBStat.id == stat_id)
    elif name := info.get("name", None) is not None:
        statement = statement.where(DBStat.name == name)
    else:
        raise ValueError("Invalid arguments for stat resolution")

    session = DB().get_session()
    stat = session.exec(statement).first()
    session.close()

    if stat is None:
        raise ValueError("Stat not found")

    stat_obj = Stat()
    stat_obj.__dict__.update(stat.__dict__)

    return stat_obj


def resolve_file(self, info: dict, file_id: int) -> File:
    """Logic to resolve a file by ID or filename."""

    statement = select(DBFile)

    if file_id is not None:
        statement = statement.where(DBFile.id == file_id)
    elif file_id := info.get("id", None) is not None:
        statement = statement.where(DBFile.id == file_id)
    elif file_id := info.get("file_id", None) is not None:
        statement = statement.where(DBFile.id == file_id)
    elif filename := info.get("filename", None) is not None:
        statement = statement.where(DBFile.filename == filename)
    else:
        raise ValueError("Invalid arguments for file resolution")
    session = DB().get_session()
    file = session.exec(statement).first()
    session.close()

    file_obj = File()
    file_obj.__dict__.update(file.__dict__)

    return file_obj


def resolve_genre(self, info: dict, genre_id: int) -> Genre:
    """Logic to resolve a genre by ID or name."""
    statement = select(DBGenre)

    if genre_id is not None:
        statement = statement.where(DBGenre.id == genre_id)
    elif genre_id := info.get("id", None) is not None:
        statement = statement.where(DBGenre.id == genre_id)
    elif genre_id := info.get("genre_id", None) is not None:
        statement = statement.where(DBGenre.id == genre_id)
    elif name := info.get("name", None) is not None:
        statement = statement.where(DBGenre.name == name)
    else:
        raise ValueError("Invalid arguments for stat resolution")

    session = DB().get_session()
    genre = session.exec(statement).first()
    session.close()

    genre_obj = Genre()
    genre_obj.__dict__.update(genre.__dict__)

    return genre_obj


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


@strawberry.type()
class Mutation:
    """Mutation class for GraphQL schema."""

    @strawberry.mutation()
    def create_user(self, info: dict) -> User:
        """Logic used to create a new user."""

        username = info.get("username", None)
        email = info.get("email", None)
        password_hash = info.get("password_hash", None)

        if username is None or email is None or password_hash is None:
            raise ValueError("Insufficient data to create a new user")

        user = DBUser(username=username, password_hash=password_hash, email=email)

        session = DB().get_session()
        session.add(user)
        session.commit()
        session.refresh(user)
        session.close()

        user_obj = User()
        user_obj.__dict__.update(user.__dict__)

        return user_obj

    @strawberry.mutation()
    def update_user(self, info: dict, user_id: int) -> User:
        """Updates user information."""
        if user_id is None:
            raise ValueError("User ID is required for updating user information")
        if not isinstance(user_id, int):
            raise ValueError("User ID must be an integer")
        if not info:
            raise ValueError("No information provided to update user")
        if "id" in info:
            raise ValueError("Cannot update user ID directly")
        if "email" in info and not isinstance(info["email"], str):
            raise ValueError("Email must be a string")
        if "username" in info and not isinstance(info["username"], str):
            raise ValueError("Username must be a string")

        # Load user from Database
        session = DB().get_session()
        user = session.exec(select(DBUser).where(DBUser.id == user_id)).first()
        # update user fields
        user = set_fields(info, user)
        # Save changes to Database
        session.add(user)
        session.commit()
        session.refresh(user)
        session.close()

        user_obj = User()
        user_obj.__dict__.update(user.__dict__)

        return user_obj

    @strawberry.mutation()
    def delete_user(self, user_id: int) -> User:
        """Deletes a user from the system."""
        if user_id is None:
            raise ValueError("User ID is required for deletion")
        if not isinstance(user_id, int):
            raise ValueError("User ID must be an integer")

        session = DB().get_session()
        user = session.exec(select(DBUser).where(DBUser.id == user_id)).first()

        if user is None:
            raise ValueError("User not found")

        session.delete(user)
        session.commit()
        session.close()

        user_obj = User()
        user_obj.__dict__.update(user.__dict__)

        return user_obj

    @strawberry.mutation()
    def update_track(self, info: dict, track_id: int) -> Track:
        """Updates information related to a track."""
        if track_id is None:
            raise ValueError("Track ID is required for updating track information")
        if not isinstance(track_id, int):
            raise ValueError("Track ID must be an integer")
        if not info:
            raise ValueError("No information provided to update track")
        if "id" in info:
            raise ValueError("Cannot update track ID directly")

        # Load track from Database
        session = DB().get_session()
        track = session.exec(select(DBTrack).where(DBTrack.id == track_id)).first()
        # update track fields
        track = set_fields(info, track)
        # Save changes to Database
        session.add(track)
        session.commit()
        session.refresh(track)
        session.close()

        track_obj = Track()
        track_obj.__dict__.update(track.__dict__)

        return track_obj

    @strawberry.mutation()
    def update_album(self, info: dict, album_id: int) -> Album:
        """Updates album information."""
        if album_id is None:
            raise ValueError("Album ID is required for updating album information")
        if not isinstance(album_id, int):
            raise ValueError("Album ID must be an integer")
        if not info:
            raise ValueError("No information provided to update album")
        if "id" in info:
            raise ValueError("Cannot update album ID directly")

        # Load album from Database
        session = DB().get_session()
        album = session.exec(select(DBAlbum).where(DBAlbum.id == album_id)).first()
        # update album fields
        album = set_fields(info, album)
        # Save changes to Database
        session.add(album)
        session.commit()
        session.refresh(album)
        session.close()

        album_obj = Album()
        album_obj.__dict__.update(album.__dict__)

        return album_obj

    @strawberry.mutation()
    def update_person(self, info: dict, person_id: int) -> Person:
        """Updates person information."""
        if person_id is None:
            raise ValueError("Person ID is required for updating person information")
        if not isinstance(person_id, int):
            raise ValueError("Person ID must be an integer")
        if not info:
            raise ValueError("No information provided to update person")
        if "id" in info:
            raise ValueError("Cannot update person ID directly")

        # Load person from Database
        session = DB().get_session()
        person = session.exec(select(DBPerson).where(DBPerson.id == person_id)).first()
        # update person fields
        person = set_fields(info, person)
        # Save changes to Database
        session.add(person)
        session.commit()
        session.refresh(person)
        session.close()

        person_obj = Person()
        person_obj.__dict__.update(person.__dict__)

        return person_obj

    @strawberry.mutation()
    def update_label(self, info: dict, label_id: int) -> Label:
        """Updates label information."""
        if label_id is None:
            raise ValueError("Label ID is required for updating label information")
        if not isinstance(label_id, int):
            raise ValueError("Label ID must be an integer")
        if not info:
            raise ValueError("No information provided to update label")
        if "id" in info:
            raise ValueError("Cannot update label ID directly")

        # Load label from Database
        session = DB().get_session()
        label = session.exec(select(DBLabel).where(DBLabel.id == label_id)).first()
        # update label fields
        label = set_fields(info, label)
        # Save changes to Database
        session.add(label)
        session.commit()
        session.refresh(label)
        session.close()

        label_obj = Label()
        label_obj.__dict__.update(label.__dict__)

        return label_obj

    @strawberry.mutation()
    def update_file(self, info: dict, file_id: int) -> File:
        """Updates file information."""
        if file_id is None:
            raise ValueError("File ID is required for updating file information")
        if not isinstance(file_id, int):
            raise ValueError("File ID must be an integer")
        if not info:
            raise ValueError("No information provided to update file")
        if "id" in info:
            raise ValueError("Cannot update file ID directly")

        # Load file from Database
        session = DB().get_session()
        file = session.exec(select(DBFile).where(DBFile.id == file_id)).first()
        # update file fields
        file = set_fields(info, file)
        # Save changes to Database
        session.add(file)
        session.commit()
        session.refresh(file)
        session.close()

        file_obj = File()
        file_obj.__dict__.update(file.__dict__)

        return file_obj

    @strawberry.mutation()
    def update_genre(self, info: dict, genre_id: int) -> Genre:
        """Updates genre information."""
        if genre_id is None:
            raise ValueError("Genre ID is required for updating genre information")
        if not isinstance(genre_id, int):
            raise ValueError("Genre ID must be an integer")
        if not info:
            raise ValueError("No information provided to update genre")
        if "id" in info:
            raise ValueError("Cannot update genre ID directly")

        # Load genre from Database
        session = DB().get_session()
        genre = session.exec(select(DBGenre).where(DBGenre.id == genre_id)).first()
        # update genre fields
        genre = set_fields(info, genre)
        # Save changes to Database
        session.add(genre)
        session.commit()
        session.refresh(genre)
        session.close()

        genre_obj = Genre()
        genre_obj.__dict__.update(genre.__dict__)

        return genre_obj
