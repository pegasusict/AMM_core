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
from enum import Enum
from datetime import datetime
from typing import List

from sqlalchemy import String
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.base import Mapped

Base = declarative_base()


class UserRole(Enum):
    """Enum for user roles."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class User(Base):
    """User model."""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash : Mapped[str] = mapped_column()
    first_name: Mapped[str] = mapped_column(default="")
    middle_name: Mapped[str] = mapped_column(default="")
    last_name: Mapped[str] = mapped_column(default="")
    is_active: Mapped[bool] = mapped_column(default=True)
    role: Mapped[Enum]= mapped_column(default=UserRole.USER.value)  # Default role is USER
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, role={self.role})>"


class ItemBase(Base):
    """ base class for item tables """
    id: Mapped[int] = mapped_column(primary_key=True)


class OptFieldBase(Base):
    """ base class for optional fields """
    id: Mapped[int] = mapped_column(primary_key=True)


#######################################################################
class Stat(ItemBase):
    """Statistics for the application."""
    __tablename__ = "Stats"

    name: Mapped[str] = mapped_column(String(30))
    value: Mapped[int] = mapped_column(default=0)
    range: Mapped["StatRange"] = relationship(back_populates="stat", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Stat {self.name}"


class StatRange(OptFieldBase):
    """Range for statistics."""
    __tablename__ = "StatRanges"

    range_start: Mapped[float] = mapped_column(default=0)
    range_end: Mapped[float] = mapped_column(default=None)

    stat: Mapped["Stat"] = relationship(back_populates="range")


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
class File(ItemBase):
    """File information."""
    __tablename__ = "Files"

    audio_ip: Mapped[str]
    import_path: Mapped[str]
    imported: Mapped[datetime] = mapped_column(default=datetime.now(UTC))
    processed: Mapped[datetime] = mapped_column(onupdate=datetime.now(UTC))
    bit_rate: Mapped[int]
    codec: Mapped[Enum] = mapped_column(Enum(Codecs))
    length: Mapped[float]
    stage: Mapped[int] = mapped_column(default=0)
    track: Mapped["Track"] = relationship(back_populates="files")
    paths: Mapped[List["FilePath"]] = relationship(back_populates="file")

    def __repr__(self) -> str:
        return f"File {self.id}"


class Track(ItemBase):
    """Track information."""
    __tablename__ = "Tracks"

    dates: Mapped[List["Date"]] = relationship(back_populates="track")
    files: Mapped[List["File"]] = relationship(back_populates="track")
    albums: Mapped[List["Album"]] = relationship(back_populates="tracks")
    key: Mapped["Key"] = relationship(back_populates="tracks")
    genres: Mapped[List["Genre"]] = relationship(back_populates="tracks")
    titles: Mapped[List["Title"]] = relationship(back_populates="track")
    mbid: Mapped["MBid"] = relationship(back_populates="track")
    performers: Mapped[List["Person"]] = relationship(back_populates="performed_tracks")
    conductors: Mapped[List["Person"]] = relationship(back_populates="conducted_tracks")
    composers: Mapped[List["Person"]] = relationship(back_populates="composed_tracks")
    lyricists: Mapped[List["Person"]] = relationship(back_populates="lyric_tracks")
    producers: Mapped[List["Person"]] = relationship(back_populates="produced_tracks")

    def __repr__(self) -> str:
        return f"Track {self.id}"


class Album(ItemBase):
    """Album information."""
    __tablename__ = "Albums"

    disc_count: Mapped[int]
    track_count: Mapped[int]
    mbid: Mapped["MBid"] = relationship(back_populates="album")
    titles: Mapped[List["Title"]] = relationship(back_populates="album")
    dates: Mapped[List["Date"]] = relationship(back_populates="album")
    label: Mapped["Label"] = relationship(back_populates="albums")
    tracks: Mapped[List["Track"]] = relationship(back_populates="albums")
    genres: Mapped[List["Genre"]] = relationship(back_populates="albums")
    performers: Mapped[List["Person"]] = relationship(back_populates="performed_albums")
    conductors: Mapped[List["Person"]] = relationship(back_populates="conducted_albums")
    composers: Mapped[List["Person"]] = relationship(back_populates="composed_albums")
    lyricists: Mapped[List["Person"]] = relationship(back_populates="lyric_albums")
    producers: Mapped[List["Person"]] = relationship(back_populates="produced_albums")
    picture: Mapped["Picture"] = relationship(back_populates="album")

    def __repr__(self) -> str:
        return f"Album {self.id}"


class Person(ItemBase):
    """Person information."""
    __tablename__ = "Persons"

    dates: Mapped[List["Date"]] = relationship(back_populates="person")
    mbid: Mapped["MBid"] = relationship(back_populates="person")
    names: Mapped[List["PersonName"]] = relationship(back_populates="person")
    picture: Mapped["Picture"] = relationship(back_populates="person")
    performed_tracks: Mapped[List["Track"]] = relationship(back_populates="performers")
    conducted_tracks: Mapped[List["Track"]] = relationship(back_populates="conductors")
    composed_tracks: Mapped[List["Track"]] = relationship(back_populates="composers")
    lyric_tracks: Mapped[List["Track"]] = relationship(back_populates="lyricists")
    produced_tracks: Mapped[List["Track"]] = relationship(back_populates="producers")
    performed_albums: Mapped[List["Album"]] = relationship(back_populates="performers")
    conducted_albums: Mapped[List["Album"]] = relationship(back_populates="conductors")
    composed_albums: Mapped[List["Album"]] = relationship(back_populates="composers")
    lyric_albums: Mapped[List["Album"]] = relationship(back_populates="lyricists")
    produced_albums: Mapped[List["Album"]] = relationship(back_populates="producers")

    def __repr__(self) -> str:
        return f"Person {self.id}"


class Label(ItemBase):
    """Label information."""
    __tablename__ = "Labels"

    name: Mapped[str]
    albums: Mapped[List["Album"]] = relationship(back_populates="label")
    owner: Mapped["Person"] = relationship(back_populates="labels")
    parent: Mapped["Label"] = relationship(back_populates="children")
    children: Mapped[List["Label"]] = relationship(back_populates="parent")

    def __repr__(self) -> str:
        return f"Label {self.id}"


class Key(ItemBase):
    """In which key the track is composed."""
    __tablename__ = "Keys"

    key: Mapped[str]
    tracks: Mapped[List["Track"]] = relationship(back_populates="key")

    def __repr__(self) -> str:
        return f"Key {self.id}"


class Genre(ItemBase):
    """Genre information."""
    __tablename__ = "Genres"

    genre: Mapped[str]
    tracks: Mapped[List["Track"]] = relationship(back_populates="genres")
    albums: Mapped[List["Album"]] = relationship(back_populates="genres")
    parents: Mapped[List["Genre"]] = relationship(back_populates="children")
    children: Mapped[List["Genre"]] = relationship(back_populates="parents")

    def __repr__(self) -> str:
        return f"Genre {self.id}"


#######################################################################
class FilePath(OptFieldBase):
    """File path information."""
    __tablename__ = "FilePaths"

    path: Mapped[str] = mapped_column(unique=True)
    definitive: Mapped[bool]
    file: Mapped["File"] = relationship(back_populates="paths")


class Date(OptFieldBase):
    """Date information."""
    __table_name__ = "Dates"

    date: Mapped[datetime]
    person: Mapped["Person"] = relationship(back_populates="dates")
    track: Mapped["Track"] = relationship(back_populates="dates")
    album: Mapped["Album"] = relationship(back_populates="dates")


class MBid(OptFieldBase):
    """MusicBrainz ID coupling."""
    __tablename__ = "MBids"

    mbid: Mapped[str] = mapped_column(String(40), unique=True)
    track: Mapped["Track"] = relationship(back_populates="mbid")
    album: Mapped["Album"] = relationship(back_populates="mbid")
    person: Mapped["Person"] = relationship(back_populates="mbid")


class TrackLyric(OptFieldBase):
    """Track lyrics."""
    __tablename__ = "TrackLyrics"

    Lyric: Mapped[str]
    track: Mapped["Track"] = relationship(back_populates="lyric")


class Title(OptFieldBase):
    """Title information."""
    __tablename__ = "Titles"

    title: Mapped[str]
    main: Mapped[bool] = mapped_column(primary_key=True)
    track: Mapped["Track"] = relationship(back_populates="titles")
    album: Mapped["Album"] = relationship(back_populates="titles")


class Picture(OptFieldBase):
    """Album/Person Pictures"""
    __tablename__ = "Pictures"

    picture_path: Mapped[str] = mapped_column(unique=True)
    album: Mapped["Album"] = relationship(back_populates="picture")
    person: Mapped["Person"] = relationship(back_populates="picture")


class PersonName(OptFieldBase):
    """Person name information."""
    __table_name__ = "PersonNames"

    name: Mapped[str]
    name_type: Mapped[enum] = mapped_column(Enum(PersonNameTypes))
    person: Mapped["Person"] = relationship(back_populates="names")

