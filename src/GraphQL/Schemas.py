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
from __future__ import annotations

from graphene import ObjectType, String, Field, Int, Float, ID, DateTime, Date as date
from graphene import Enum, InputObjectType, Boolean, List

from ..models import UserRole, Codecs, DateTypes

class User(ObjectType):
    """User type for GraphQL schema."""
    id = ID()
    username = String()
    email = String()
    first_name = String()
    middle_name = String()
    last_name = String()
    role = Enum(UserRole)
    created_at = DateTime()
    updated_at = DateTime()
    is_active = Boolean()
class UserInput(InputObjectType):
    """Input type for creating or updating a user."""
    username = String(required=True)
    email = String(required=True)
    password_hash = String(required=True)
    first_name = String()
    middle_name = String()
    last_name = String()
    role = String()
    is_active = Boolean()
    updated_at = DateTime()
    id = ID()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = kwargs.get('id', None)
        self.username = kwargs.get('username', None)
        self.email = kwargs.get('email', None)
        self.password_hash = kwargs.get('password_hash', None)
        self.first_name = kwargs.get('first_name', None)
        self.middle_name = kwargs.get('middle_name', None)
        self.last_name = kwargs.get('last_name', None)
        self.role = kwargs.get('role', None)
        self.is_active = kwargs.get('is_active', None)
        self.created_at = kwargs.get('created_at', None)
        self.updated_at = kwargs.get('updated_at', None)

class Stat(ObjectType):
    """Stat type for GraphQL schema."""
    id = ID()
    name = String()
    value = Float()
    range_start = Float()
    range_end = Float()
    created_at = DateTime()
    updated_at = DateTime()

class File(ObjectType):
    """File type for GraphQL schema."""
    id = ID()
    imported = DateTime()
    processed = DateTime()
    file_path = String()
    file_name = String()
    file_type = String()
    file_extension = String()
    size = Int()
    created_at = DateTime()
    updated_at = DateTime()
    codec = Enum(Codecs)
    bitrate = Int()
    sample_rate = Int()
    channels = Int()
    length = Int()
    stage = Int()

class Track(ObjectType):
    """Track type for GraphQL schema."""
    id = ID()
    title = String()
    subtitle = String()
    artists = List(Person)
    year = Int()
    albums = List(Album)
    files = List(File)
    key = String()
    dates = List(Date)
    genres = List(Genre)
    mbid = String(MBid)
    label = String()
    lyrics = String()

class Album(ObjectType):
    """Album type for GraphQL schema."""
    id = ID()
    title = String()
    subtitle = String()
    artists = List(Person)
    tracks = List(Track)
    key = String()
    dates = List(Date)
    genres = List(Genre)
    mbid = String()
    label = String()
    picture = String()
    disc_count = Int()
    track_count = Int()
    picture = String()
    release_date = Date()
    release_country = String()

class Genre(ObjectType):
    """Genre type for GraphQL schema."""
    id = ID()
    name = String()
    description = String()
    created_at = DateTime()
    updated_at = DateTime()
    albums = List(Album)
    tracks = List(Track)

class Person(ObjectType):
    """Person type for GraphQL schema."""
    id = ID()
    first_name = String()
    middle_name = String()
    last_name = String()
    alias = String()
    nick_name = String()
    date_of_birth = date()
    date_of_death = date()
    picture = String()
    mbid = String()
    performed_tracks = List(Track)
    performed_albums = List(Album)  

class Date(ObjectType):
    """Date type for GraphQL schema."""
    id = ID()
    date = date()
    type = Enum(DateTypes)
    person = Field(Person)
    track = Field(Track)
    album = Field(Album)

class Label(ObjectType):
    """Label type for GraphQL schema."""
    id = ID()
    name = String()
    description = String()
    created_at = DateTime()
    updated_at = DateTime()
    albums = List(Album)

class Key(ObjectType):
    """Key type for GraphQL schema."""
    id = ID()
    name = String()

class FilePath(ObjectType):
    """FilePath type for GraphQL schema."""
    id = ID()
    path = String()
    definitive = Boolean()
    file = Field(File)

class MBid(ObjectType):
    """MBid type for GraphQL schema."""
    id = ID()
    mbid = String()
    track = Field(Track)
    album = Field(Album)
    person = Field(Person)
    label = Field(Label)
