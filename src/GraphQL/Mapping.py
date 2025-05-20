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

from Singletons.database import DB
from Schemas import Track, Album, User, Person, Label, Stat, File, Genre
from models import DBAlbum, DBFile, DBGenre, DBLabel, DBPerson, DBTrack, DBUser

#################################################################################

def set_fields(info: dict, subject: object) -> object:
    """Sets al non-empty values to the object."""
    for key, value in info:
        if key == "id":
            continue
        if value is not None:
            if hasattr(subject, key):
                subject.key = value # type: ignore
    return subject

def db_mutation(obj: object, result: object, refresh: bool = True) -> object:
    """Executes the DB mutation and returns the object."""
    session = DB().get_session()
    session.add(obj)
    session.commit()
    if refresh:
        obj = session.refresh(instance=obj)
    session.close()
    result.__dict__.update(obj.__dict__)
    return result


#################################################################################
def resolve_user(self, info: dict) -> User:
    """Logic to resolve a user."""
    user_id = info.get("user_id", None)
    if user_id is not None:
        return User(id=user_id)
    username = info.get("username", None)
    if username is not None:
        return User(username=username)
    email = info.get("email", None)
    if email is not None:
        return User(email=email)
    raise ValueError("Invalid arguments for user resolution")

def resolve_track(self, info: dict, track_id: int) -> Track:
    """Logic to resolve a track by ID."""
    if track_id is not None:
        return Track(id=track_id)
    mbid = info.get("mbid", None)
    if mbid is not None:
        return Track(mbid=mbid)
    title = info.get("title", None)
    artist = info.get("artist", None)
    if title is not None and artist is not None:
        return Track(title=title, artist=artist)
    album_id = info.get("album_id", None)
    track_no = info.get("track_no", None)
    if album_id is not None and track_no is not None:
        return Track(album_id=album_id, track_no=track_no)
    raise ValueError("Invalid arguments for track resolution")

def resolve_album(self, info: dict, album_id: int) -> Album:
    """Logic to resolve an album by ID."""
    if album_id is not None:
        return Album(id=album_id)
    mbid = info.get("mbid", None)
    if mbid is not None:
        return Album(mbid=mbid)
    title = info.get("title", None)
    artist = info.get("artist", None)
    if title is not None and artist is not None:
        return Album(title=title, artist=artist)
    release_date = info.get("release_date", None)
    if release_date is not None:
        return Album(release_date=release_date)
    raise ValueError("Invalid arguments for album resolution")

def resolve_person(self, info: dict, person_id: int) -> Person:
    """Logic to resolve a person by ID."""
    if person_id is not None:
        return Person(id=person_id)
    name = info.get("name", None)
    if name is not None:
        return Person(name=name)
    nickname = info.get("nickname", None)
    if nickname is not None:
        return Person(nickname=nickname)
    birth_date = info.get("birth_date", None)
    if birth_date is not None:
        return Person(birth_date=birth_date)
    raise ValueError("Invalid arguments for person resolution")

def resolve_label(self, info: dict, label_id: int) -> Label:
    """Logic to resolve a label by ID."""
    if label_id is not None:
        return Label(id=label_id)
    name = info.get("name", None)
    if name is not None:
        return Label(name=name)
    raise ValueError("Invalid arguments for label resolution")

def resolve_stat(self, info: dict, stat_id: int) -> Stat:
    """Logic to resolve a stat by ID."""
    if stat_id is not None:
        return Stat(id=stat_id)
    name=info.get("name", None)
    if name is not None:
        return Stat(name=name)
    raise ValueError("Invalid arguments for stat resolution")

def resolve_file(self, info: dict, file_id: int) -> File:
    """Logic to resolve a file by ID."""
    if file_id is not None:
        return File(id=file_id)
    filename=info.get("filename", None)
    if filename is not None:
        return Stat(filename=filename)
    raise ValueError("Invalid arguments for stat resolution")

def resolve_genre(self, info: dict, genre_id: int) -> Genre:
    """Logic to resolve a genre by ID."""
    if genre_id is not None:
        return Genre(id=genre_id)
    name=info.get("name", None)
    if name is not None:
        return Genre(name=name)
    raise ValueError("Invalid arguments for stat resolution")

@strawberry.type()
class Query():
    """Query class for GraphQL schema."""
    track:str = strawberry.field(resolve_track) # type: ignore
    album:str = strawberry.field(resolve_album) # type: ignore
    person:str = strawberry.field(resolve_person) # type: ignore
    user:str = strawberry.field(resolve_user) # type: ignore
    label:str = strawberry.field(resolve_label) # type: ignore
    stat:str = strawberry.field(resolve_stat) # type: ignore
    file:str = strawberry.field(resolve_file) # type: ignore
    genre:str = strawberry.field(resolve_genre) # type: ignore

@strawberry.type()
class Mutation():
    """Mutation class for GraphQL schema."""

    @strawberry.mutation()
    def create_user(self, info: dict) -> User:
        """Logic used to create a new user."""
        username = info.get("username", None)
        email = info.get("email", None)
        password_hash = info.get("password_hash", None)
        if username is None or email is None or password_hash is None:
            raise ValueError("Insufficient data to create a new user")
        user = DBUser(username=username,password_hash=password_hash,email=email)
        return db_mutation(user,User()) # type: ignore

    def update_user(self, info: dict, user_id: int) -> User:
        """Updates user information."""
        user = DBUser(id=user_id)
        user = set_fields(info, user)
        return db_mutation(user, User()) # type: ignore

    def delete_user(self, user_id: int) -> User:
        """Deletes a user from the system."""
        user = DBUser(id=user_id)
        # TODO: actually delete user from DB
        return db_mutation(user, User(), False) # type: ignore

    def update_track(self, info: dict, track_id: int) -> Track:
        """Updates information related to a track."""
        track = DBTrack(id=track_id)
        track = set_fields(info, track)
        return db_mutation(track, Track()) # type: ignore

    def update_album(self, info: dict, album_id: int) -> Album:
        """Updates album information."""
        album = DBAlbum(id=album_id)
        album = set_fields(info, album)
        return db_mutation(album, Album()) # type: ignore

    def update_person(self, info: dict, person_id: int) -> Person:
        """Updates person information."""
        person = DBPerson(id=person_id)
        person = set_fields(info, person)
        return db_mutation(person, Person()) # type: ignore

    def update_label(self, info: dict, label_id: int) -> Label:
        """Updates label information."""
        label = DBLabel(id=label_id)
        label = set_fields(info, label)
        return db_mutation(label, Label()) # type: ignore

    def update_file(self, info: dict, file_id: int) -> File:
        """Updates file information."""
        file = DBFile(id=file_id)
        file = set_fields(info, file)
        return db_mutation(file, File()) # type: ignore

    def update_genre(self, info: dict, genre_id: int) -> Genre:
        """Updates genre information."""
        genre = DBGenre(id=genre_id)
        genre = set_fields(info, genre)
        return db_mutation(genre, Genre()) # type: ignore
