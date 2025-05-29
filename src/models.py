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
import datetime
from typing import List, Optional
from multiprocessing import Process

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, String

from .Singletons.database import DB


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


class TaskType(Enum):
    """Enum for different task types."""
    ART_GETTER = "art_getter"
    IMPORTER = "importer"
    TAGGER = "tagger"
    FINGERPRINTER = "fingerprinter"
    EXPORTER = "exporter"
    LYRICS_GETTER = "lyrics_getter"
    NORMALIZER = "normalizer"
    TRIMMER = "trimmer"
    CONVERTER = "converter"
    PARSER = "parser"

class TaskStatus(Enum):
    """Enum for different task statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Codecs(Enum):
    """Codec types for audio files."""
    WAV = 0
    WMA = 1
    MP3 = 2
    MP4 = 3
    FLAC = 4
    ASF = 5
    OGG = 6
    AAC = 7
    APE = 8
    AIFF = 9
    UNKNOWN = 99

class Stages(Enum):
    """Stages of processing."""
    NONE = 0
    IMPORTED = 1
    FINGERPRINTED = 2
    TAGS_RETRIEVED = 3
    ART_RETRIEVED = 4 # TODO: is Album/artist related, but album is needed for file
    LYRICS_RETRIEVED = 5 # TODO: is track related, but needed for file...
    TRIMMED = 6
    NORMALIZED = 7
    TAGGED = 8
    SORTED = 9

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

class TitleType(Enum):
    """Types of titles"""
    TITLE = 0
    TITLE_SORT = 1
    SUB_TITLE = 2

######################################################################
class DBUser(SQLModel, table=True):
    """User model."""
    __tablename__ = "users" # type: ignore

    id: Optional[int] = Field(primary_key=True, index=True, default=None)
    username: str = Field(unique=True, default="")
    email: str = Field(unique=True, default="")
    password_hash : str = Field(default="")
    first_name: str = Field(default="")
    middle_name: str = Field(default="")
    last_name: str = Field(default="")
    date_of_birth: datetime.datetime = Field(default="")
    is_active: bool = Field(default=True)
    role: Enum = Field(default=UserRole.USER.value)  # Default role is USER
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
                                        sa_column_kwargs={"onupdate": lambda: datetime.datetime.now(datetime.timezone.utc)})

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, role={self.role})>"
#######################################################################
class DBTask(SQLModel, table=True):
    """DB Model for Task."""
    __tablename__ = "tasks"  # type: ignore

    id: int = Field(int, primary_key=True, unique=True)
    task_id:str = Field(String, nullable=False)
    start_time:datetime.datetime
    end_time:datetime.datetime
    duration:int
    batch_files:List["DBFile"] = Relationship(back_populates="task")
    batch_tracks:List["DBTrack"] = Relationship(back_populates="task")
    batch_albums:List["DBAlbum"] = Relationship(back_populates="task")
    batch_persons:List["DBPerson"] = Relationship(back_populates="task")
    processed:int
    progress:float
    process:Process
    result:str
    error:str
    status:Enum = Field(Enum(TaskStatus))
    task_type:Enum = Field(Enum(TaskType))
########################################################################
class ItemBase(SQLModel):
    """ base class for item tables """
    id: int = Field(default=None, primary_key=True, index=True)
class OptFieldBase(SQLModel):
    """ base class for optional fields """
    id: int = Field(default=None, primary_key=True, index=True)
#######################################################################
class DBStat(ItemBase, table=True):
    """Statistics for the application."""
    __tablename__ = "stats"  # type: ignore

    name: str = Field(String(30))
    value: int = Field(default=0)
    range: Optional[DBStatRange] = Relationship(back_populates="stat")

    def __repr__(self) -> str:
        return f"Stat {self.name}"
class DBStatRange(OptFieldBase, table=True):
    """Range for statistics."""
    __tablename__ = "stat_ranges"  # type: ignore

    range_start: float = Field(default=0)
    range_end: float = Field(default=None)

    stat: Optional["DBStat"] = Relationship(back_populates="range")
#######################################################################
class DBFile(ItemBase, table=True):
    """File information."""
    __tablename__ = "files"  # type: ignore

    audio_ip: str = Field(default = None)
    imported: datetime.datetime = Field(default=datetime.datetime.now(datetime.timezone.utc))
    processed: datetime.datetime = Field(
        default=None,
        sa_column_kwargs={"onupdate": datetime.datetime.now(datetime.timezone.utc)}
    )
    bitrate: int = Field(default = None)
    sample_rate: int = Field(default = None)
    channels: int = Field(default = None)
    file_type: str = Field(default = None)
    file_size: int = Field(default = None)
    file_name: str = Field(default = None)
    file_extension: str = Field(default = None)
    codec: Enum = Field(Enum(Codecs), default=Codecs.UNKNOWN) # type: ignore
    length: int = Field(default = None)
    track: DBTrack = Relationship(back_populates="files")
    paths: List["DBFilePath"] = Relationship(back_populates="file")
    task: DBTask = Relationship(back_populates="batch_files")
    stage: Enum = Field(Enum(Stages),default = Stages.NONE) # type: ignore

    def __repr__(self) -> str:
        return f"File {self.id}"

class Track(BaseModel):
    """Operational Track Data class."""
    id:Optional[int] = None
    title:str = ""
    title_sort:str = ""
    subtitle:Optional[str] = ""
    artists:List[str] = [""]
    albums:List[str] = [""]
    key:str = ""
    genres:List[str] = [""]
    fingerprint:str = "" # get from filedata
    mbid:str = ""
    conductors:List[str] = [""]
    composers:List[str] = [""]
    lyricists:List[str] = [""]
    releasedate:datetime.date = datetime.date(1900,1,1)
    producers:List[str] = [""]
    task:str = ""
    file:str = ""

    def __init__(self, track_id:int|None = None) -> None:
        if track_id is not None:
            session = DB().get_session()
            trackdata = session.get_one(DBTrack, track_id)
            for key, value in trackdata:
                setattr(self, key, value)

    def get_tags(self) -> dict[str, str|int|datetime.date]:
        """Gets all the tagdata, converts if nessecary and
        returns it as a dictionairy"""
        result = {}

        result["title"] = self.title
        result["subtitle"] = self.subtitle
        result["artists"] = ','.join(map(str, self.artists))
        result["albums"] = ','.join(map(str, self.albums))
        result["key"] = self.key
        result["genres"] = ','.join(map(str, self.genres))
        result["fingerprint"] = self.fingerprint
        result["mbid"] = self.mbid
        result["conductors"] = ','.join(map(str, self.conductors))
        result["composers"] = ','.join(map(str, self.composers))
        result["lyricists"] = ','.join(map(str, self.lyricists))
        result["releasedate"] = self.releasedate
        result["producers"] = ','.join(map(str, self.producers))

        return result

class DBTrack(ItemBase, table=True):
    """Track information."""
    __tablename__ = "tracks"  # type: ignore

    dates: List["DBDate"] = Relationship(back_populates="track")
    files: List["DBFile"] = Relationship(back_populates="track")
    albums: List["DBAlbum"] = Relationship(back_populates="tracks")
    key: "DBKey" = Relationship(back_populates="tracks")
    genres: List["DBGenre"] = Relationship(back_populates="tracks")
    titles: List["DBTitle"] = Relationship(back_populates="track")
    mbid: "DBMBid" = Relationship(back_populates="track")
    performers: List["DBPerson"] = Relationship(back_populates="performed_tracks")
    conductors: List["DBPerson"] = Relationship(back_populates="conducted_tracks")
    composers: List["DBPerson"] = Relationship(back_populates="composed_tracks")
    lyricists: List["DBPerson"] = Relationship(back_populates="lyric_tracks")
    producers: List["DBPerson"] = Relationship(back_populates="produced_tracks")
    task: DBTask = Relationship(back_populates="batch_tracks")

    def __repr__(self) -> str:
        return f"Track {self.id}"

class DBAlbum(ItemBase, table=True):
    """Album information."""
    __tablename__ = "albums"  # type: ignore

    disc_count: int = Field(default=0)
    track_count: int = Field(default=0)
    mbid: "DBMBid" = Relationship(back_populates="album")
    titles: List["DBTitle"] = Relationship(back_populates="album")
    dates: List["DBDate"] = Relationship(back_populates="album")
    label: "DBLabel" = Relationship(back_populates="albums")
    tracks: List["DBTrack"] = Relationship(back_populates="albums")
    genres: List["DBGenre"] = Relationship(back_populates="albums")
    performers: List["DBPerson"] = Relationship(back_populates="performed_albums")
    conductors: List["DBPerson"] = Relationship(back_populates="conducted_albums")
    composers: List["DBPerson"] = Relationship(back_populates="composed_albums")
    lyricists: List["DBPerson"] = Relationship(back_populates="lyric_albums")
    producers: List["DBPerson"] = Relationship(back_populates="produced_albums")
    picture: "DBPicture" = Relationship(back_populates="album")
    task: DBTask = Relationship(back_populates="batch_albums")

    def __repr__(self) -> str:
        return f"Album {self.id}"

class DBPerson(ItemBase, table=True):
    """Person information."""
    __tablename__ = "persons"  # type: ignore

    dates: List["DBDate"] = Relationship(back_populates="person")
    mbid: "DBMBid" = Relationship(back_populates="person")
    names: List["DBPersonName"] = Relationship(back_populates="person")
    picture: "DBPicture" = Relationship(back_populates="person")
    performed_tracks: List["DBTrack"] = Relationship(back_populates="performers")
    conducted_tracks: List["DBTrack"] = Relationship(back_populates="conductors")
    composed_tracks: List["DBTrack"] = Relationship(back_populates="composers")
    lyric_tracks: List["DBTrack"] = Relationship(back_populates="lyricists")
    produced_tracks: List["DBTrack"] = Relationship(back_populates="producers")
    performed_albums: List["DBAlbum"] = Relationship(back_populates="performers")
    conducted_albums: List["DBAlbum"] = Relationship(back_populates="conductors")
    composed_albums: List["DBAlbum"] = Relationship(back_populates="composers")
    lyric_albums: List["DBAlbum"] = Relationship(back_populates="lyricists")
    produced_albums: List["DBAlbum"] = Relationship(back_populates="producers")
    task: DBTask = Relationship(back_populates="batch_persons")

    def __repr__(self) -> str:
        return f"Person {self.id}"

class DBLabel(ItemBase, table=True):
    """Label information."""
    __tablename__ = "labels"  # type: ignore

    name: str = Field(default="")
    mbid: "DBMBid" = Relationship(back_populates="label")
    albums: List["DBAlbum"] = Relationship(back_populates="label")
    owner: "DBPerson" = Relationship(back_populates="labels")
    parent: "DBLabel" = Relationship(back_populates="children")
    children: List["DBLabel"] = Relationship(back_populates="parent")

    def __repr__(self) -> str:
        return f"Label {self.id}"

class DBKey(ItemBase, table=True):
    """In which key the track is composed."""
    __tablename__ = "keys"  # type: ignore

    key: str
    tracks: List["DBTrack"] = Relationship(back_populates="key")

    def __repr__(self) -> str:
        return f"Key {self.id}"

class DBGenre(ItemBase, table=True):
    """Genre information."""
    __tablename__ = "genres"  # type: ignore

    genre: str = Field(default="")
    tracks: List["DBTrack"] = Relationship(back_populates="genres")
    albums: List["DBAlbum"] = Relationship(back_populates="genres")
    parents: List["DBGenre"] = Relationship(back_populates="children")
    children: List["DBGenre"] = Relationship(back_populates="parents")

    def __repr__(self) -> str:
        return f"Genre {self.id}"
#######################################################################
class DBFilePath(OptFieldBase, table=True):
    """File path information."""
    __tablename__ = "filepaths"  # type: ignore

    path: str = Field(unique=True)
    definitive: bool
    file: "DBFile" = Relationship(back_populates="paths")

class DBDate(OptFieldBase, table=True):
    """Date information."""
    __tablename__ = "dates"  # type: ignore

    date: datetime.date
    type: Enum = Field(Enum(DateTypes))
    person: "DBPerson" = Relationship(back_populates="dates")
    track: "DBTrack" = Relationship(back_populates="dates")
    album: "DBAlbum" = Relationship(back_populates="dates")

class DBMBid(OptFieldBase, table=True):
    """MusicBrainz ID coupling."""
    __tablename__ = "mbids"  # type: ignore

    mbid: str = Field(String(40), unique=True)
    track: "DBTrack" = Relationship(back_populates="mbid")
    album: "DBAlbum" = Relationship(back_populates="mbid")
    person: "DBPerson" = Relationship(back_populates="mbid")
    label: "DBLabel" = Relationship(back_populates="mbid")

class DBTrackLyric(OptFieldBase, table=True):
    """Track lyrics."""
    __tablename__ = "track_lyrics"  # type: ignore

    Lyric: str
    track: "DBTrack" = Relationship(back_populates="lyric")

class DBTitle(OptFieldBase, table=True):
    """Title information."""
    __tablename__ = "titles"  # type: ignore

    title: str
    title_type:Enum=Field(Enum(TitleType))
    track: "DBTrack" = Relationship(back_populates="titles")
    album: "DBAlbum" = Relationship(back_populates="titles")

class DBPicture(OptFieldBase, table=True):
    """Album/Person Pictures"""
    __tablename__ = "pictures"  # type: ignore

    picture_path: str = Field(unique=True)
    album: "DBAlbum" = Relationship(back_populates="picture")
    person: "DBPerson" = Relationship(back_populates="picture")

class DBPersonName(OptFieldBase, table=True):
    """Person name information."""
    __tablename__ = "person_names"  # type: ignore

    name: str
    name_type: Enum = Field(Enum(PersonNameTypes))
    person: "DBPerson" = Relationship(back_populates="names")
