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

"""Database Models for the application."""
from __future__ import annotations
from enum import Enum
from datetime import datetime
from typing import List, Optional

from sqlmodel import SQLModel, Field, Relationship, String


class UserRole(Enum):
    """Enum for user roles."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    
    @classmethod
    def get_choices(cls):
        """
        Get choices for the enum.
        """
        return [(role.value, role.name) for role in cls]

class User(SQLModel, table=True):
    """User model."""

    id: Optional[int] = Field(primary_key=True, index=True)
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    password_hash : str
    first_name: str = Field(default="")
    middle_name: str = Field(default="")
    last_name: str = Field(default="")
    date_of_birth: datetime
    is_active: bool
    role: Enum = Field(default=UserRole.USER.value)  # Default role is USER
    created_at: datetime = Field(default=datetime.utcnow)
    updated_at: datetime = Field(default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, role={self.role})>"

########################################################################
class ItemBase(SQLModel):
    """ base class for item tables """
    id: int = Field(primary_key=True, index=True)
class OptFieldBase(SQLModel):
    """ base class for optional fields """
    id: int = Field(primary_key=True, index=True)
#######################################################################
class Stat(ItemBase, table=True):
    """Statistics for the application."""

    name: str = Field(String(30))
    value: int = Field(default=0)
    range: Optional[StatRange] = Relationship(back_populates="stat", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Stat {self.name}"

class StatRange(OptFieldBase, table=True):
    """Range for statistics."""

    range_start: float = Field(default=0)
    range_end: float = Field(default=None)

    stat: Optional["Stat"] = Relationship(back_populates="range")
#######################################################################
class Codecs(Enum):
    """Codec types for audio files."""
    WAV = 0
    WMA = 1
    MP2 = 2
    MP3 = 3
    MP4 = 4
    M4A = 5
    FLAC = 6
    ASF = 7
    OGG = 8
    AAC = 9
    APE = 10
    AIFF = 11
    WAVE = 12

class PersonNameTypes(Enum):
    """Types of person names."""
    FULL_NAME = 0
    SORT_NAME = 1
    FIRST_NAME = 2
    MIDDLE_NAME = 3
    LAST_NAME = 4
    NICK_NAME = 5
    ALIAS = 6

class DateTypes(Enum):
    """Types of dates."""
    COMPOSE = 0
    RELEASE = 1
    JOINED = 2
    LEFT = 3
    BORN = 4
    DECEASED = 5
#######################################################################
class File(ItemBase, table=True):
    """File information."""

    audio_ip: str
    imported: datetime = Field(default=datetime.utcnow())
    processed: datetime = Field(onupdate=datetime.utcnow())
    bitrate: int
    sample_rate: int
    channels: int
    file_type: str
    file_size: int
    file_name: str
    file_extension: str
    codec: Enum = Field(Enum(Codecs))
    length: int
    stage: int = Field(default=0)
    track: Track = Relationship(back_populates="files")
    paths: List["FilePath"] = Relationship(back_populates="file")

    def __repr__(self) -> str:
        return f"File {self.id}"

class Track(ItemBase, table=True):
    """Track information."""
    dates: List["Date"] = Relationship(back_populates="track")
    files: List["File"] = Relationship(back_populates="track")
    albums: List["Album"] = Relationship(back_populates="tracks")
    key: "Key" = Relationship(back_populates="tracks")
    genres: List["Genre"] = Relationship(back_populates="tracks")
    titles: List["Title"] = Relationship(back_populates="track")
    mbid: "MBid" = Relationship(back_populates="track")
    performers: List["Person"] = Relationship(back_populates="performed_tracks")
    conductors: List["Person"] = Relationship(back_populates="conducted_tracks")
    composers: List["Person"] = Relationship(back_populates="composed_tracks")
    lyricists: List["Person"] = Relationship(back_populates="lyric_tracks")
    producers: List["Person"] = Relationship(back_populates="produced_tracks")

    def __repr__(self) -> str: return f"Track {self.id}"

class Album(ItemBase, table=True):
    """Album information."""
    disc_count: int
    track_count: int
    mbid: "MBid" = Relationship(back_populates="album")
    titles: List["Title"] = Relationship(back_populates="album")
    dates: List["Date"] = Relationship(back_populates="album")
    label: "Label" = Relationship(back_populates="albums")
    tracks: List["Track"] = Relationship(back_populates="albums")
    genres: List["Genre"] = Relationship(back_populates="albums")
    performers: List["Person"] = Relationship(back_populates="performed_albums")
    conductors: List["Person"] = Relationship(back_populates="conducted_albums")
    composers: List["Person"] = Relationship(back_populates="composed_albums")
    lyricists: List["Person"] = Relationship(back_populates="lyric_albums")
    producers: List["Person"] = Relationship(back_populates="produced_albums")
    picture: "Picture" = Relationship(back_populates="album")

    def __repr__(self) -> str:
        return f"Album {self.id}"

class Person(ItemBase, table=True):
    """Person information."""
    dates: List["Date"] = Relationship(back_populates="person")
    mbid: "MBid" = Relationship(back_populates="person")
    names: List["PersonName"] = Relationship(back_populates="person")
    picture: "Picture" = Relationship(back_populates="person")
    performed_tracks: List["Track"] = Relationship(back_populates="performers")
    conducted_tracks: List["Track"] = Relationship(back_populates="conductors")
    composed_tracks: List["Track"] = Relationship(back_populates="composers")
    lyric_tracks: List["Track"] = Relationship(back_populates="lyricists")
    produced_tracks: List["Track"] = Relationship(back_populates="producers")
    performed_albums: List["Album"] = Relationship(back_populates="performers")
    conducted_albums: List["Album"] = Relationship(back_populates="conductors")
    composed_albums: List["Album"] = Relationship(back_populates="composers")
    lyric_albums: List["Album"] = Relationship(back_populates="lyricists")
    produced_albums: List["Album"] = Relationship(back_populates="producers")

    def __repr__(self) -> str:
        return f"Person {self.id}"

class Label(ItemBase, table=True):
    """Label information."""
    name: str
    mbid: "MBid" = Relationship(back_populates="label")
    albums: List["Album"] = Relationship(back_populates="label")
    owner: "Person" = Relationship(back_populates="labels")
    parent: "Label" = Relationship(back_populates="children")
    children: List["Label"] = Relationship(back_populates="parent")

    def __repr__(self) -> str:
        return f"Label {self.id}"

class Key(ItemBase, table=True):
    """In which key the track is composed."""
    key: str
    tracks: List["Track"] = Relationship(back_populates="key")

    def __repr__(self) -> str:
        return f"Key {self.id}"

class Genre(ItemBase, table=True):
    """Genre information."""
    genre: str
    tracks: List["Track"] = Relationship(back_populates="genres")
    albums: List["Album"] = Relationship(back_populates="genres")
    parents: List["Genre"] = Relationship(back_populates="children")
    children: List["Genre"] = Relationship(back_populates="parents")

    def __repr__(self) -> str:
        return f"Genre {self.id}"
#######################################################################
class FilePath(OptFieldBase, table=True):
    """File path information."""
    path: str = Field(unique=True)
    definitive: bool
    file: "File" = Relationship(back_populates="paths")

class Date(OptFieldBase, table=True):
    """Date information."""
    date: datetime
    type: Enum = Field(Enum(DateTypes))
    person: "Person" = Relationship(back_populates="dates")
    track: "Track" = Relationship(back_populates="dates")
    album: "Album" = Relationship(back_populates="dates")

class MBid(OptFieldBase, table=True):
    """MusicBrainz ID coupling."""
    mbid: str = Field(String(40), unique=True)
    track: "Track" = Relationship(back_populates="mbid")
    album: "Album" = Relationship(back_populates="mbid")
    person: "Person" = Relationship(back_populates="mbid")
    label: "Label" = Relationship(back_populates="mbid")

class TrackLyric(OptFieldBase, table=True):
    """Track lyrics."""
    Lyric: str
    track: "Track" = Relationship(back_populates="lyric")

class Title(OptFieldBase, table=True):
    """Title information."""
    title: str
    main: bool = Field(primary_key=True)
    track: "Track" = Relationship(back_populates="titles")
    album: "Album" = Relationship(back_populates="titles")

class Picture(OptFieldBase, table=True):
    """Album/Person Pictures"""
    picture_path: str = Field(unique=True)
    album: "Album" = Relationship(back_populates="picture")
    person: "Person" = Relationship(back_populates="picture")

class PersonName(OptFieldBase, table=True):
    """Person name information."""
    name: str
    name_type: Enum = Field(Enum(PersonNameTypes))
    person: "Person" = Relationship(back_populates="names")

