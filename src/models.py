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
import datetime as dt
from enum import StrEnum
from pathlib import Path
from typing import Any, List, Optional
from multiprocessing import Process

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, String

from Enums import (
    UserRole,
    TaskType,
    TaskStatus,
    Codec,
    Stage,
    PersonNameType,
    DateType,
    TitleType,
)
from .Tasks.art_getter import ArtType
from .Exceptions import InvalidValueError
from .Tasks.task import Task
from .Singletons.database import DB


class DBUser(SQLModel, table=True):
    """User model."""

    __tablename__ = "users"  # type: ignore

    id: Optional[int] = Field(primary_key=True, index=True, default=None)
    username: str = Field(unique=True, default="")
    email: str = Field(unique=True, default="")
    password_hash: str = Field(default="")
    first_name: str = Field(default="")
    middle_name: str = Field(default="")
    last_name: str = Field(default="")
    date_of_birth: dt.datetime = Field(default="")
    is_active: bool = Field(default=True)
    role: StrEnum = Field(default=UserRole.USER.value)  # Default role is USER
    created_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc)
    )
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc),
        sa_column_kwargs={"onupdate": lambda: dt.datetime.now(dt.timezone.utc)},
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, role={self.role})>"


#######################################################################
class DBFileToConvert(SQLModel, table=True):
    """DB Model for files to convert."""

    __tablename__ = "files_to_convert"  # type: ignore

    file: "DBFile" = Relationship(back_populates="batch_convert")
    codec: StrEnum = Field(StrEnum(Codec), default=Codec.UNKNOWN)  # type: ignore
    task: "DBTask" = Relationship(back_populates="batch_convert")


class DBTask(SQLModel, table=True):
    """DB Model for Task."""

    __tablename__ = "tasks"  # type: ignore

    id: int = Field(default=None, sa_type=int, primary_key=True, unique=True)
    task_id: str = Field(default="", sa_type=String, nullable=False)
    start_time: dt.datetime = Field(default=None)
    end_time: dt.datetime = Field(default=None)
    duration: int = Field(default=0, sa_type=int)
    batch_files: List["DBFile"] = Relationship(back_populates="task")
    batch_tracks: List["DBTrack"] = Relationship(back_populates="task")
    batch_albums: List["DBAlbum"] = Relationship(back_populates="task")
    batch_persons: List["DBPerson"] = Relationship(back_populates="task")
    batch_convert: List["DBFileToConvert"] = Relationship(back_populates="task")
    processed: int = Field(default=0, sa_type=int)
    progress: float = Field(default=0, sa_type=float)
    process: Process = Field(default=None, sa_type=Process)
    function: str = Field(default="", sa_type=String)
    kwargs: str = Field(default="", sa_type=String)
    result: str = Field(default="", sa_type=String)
    error: str = Field(default="", sa_type=String)
    status: StrEnum = Field(StrEnum(TaskStatus), default=TaskStatus.PENDING)  # type: ignore
    task_type: StrEnum = Field(StrEnum(TaskType), default=TaskType.CUSTOM)  # type: ignore

    required_fields = (
        "task_id",
        "start_time",
        "end_time",
        "duration",
        "processed",
        "progress",
        "process",
        "function",
        "result",
        "error",
        "status",
        "task_type",
    )

    def fill_required_fields(self, task: Task) -> None:
        """
        Checks if all required fields are set.

        Raises:
            ValueError: If any required field is missing.
        """
        for field in self.required_fields:
            if not hasattr(self, field):
                raise ValueError(f"Task is missing required attribute: {field}")
            setattr(self, field, getattr(task, field))

    def validate_art_type(self, art_type: ArtType) -> None:
        """
        Validates the art type.

        Raises:
            InvalidValueError: If the art type is not valid.
        """
        if art_type not in ArtType:
            raise InvalidValueError(f"Invalid task type: {art_type}")

    def import_task(self, task: Task) -> None:
        """
        Imports a task into the database.

        Args:
            task: The task to import.
        """
        self.fill_required_fields(task)
        match task.task_type:
            case TaskType.ART_GETTER:
                for mbid, art_type in task.batch:  # type: ignore
                    if art_type == ArtType.ALBUM:
                        self.batch_albums = [DBAlbum(mbid=mbid)]  # type: ignore
                    else:
                        self.batch_persons = [DBPerson(mbid=mbid)]  # type: ignore
            case TaskType.TAGGER | TaskType.LYRICS_GETTER | TaskType.DEDUPER:
                self.batch_tracks = [DBTrack(id=track_id) for track_id in task.batch]  # type: ignore
            case TaskType.FINGERPRINTER | TaskType.EXPORTER | TaskType.NORMALIZER:
                self.batch_files = [DBFile(id=file_id) for file_id in task.batch]  # type: ignore
            case TaskType.TRIMMER | TaskType.PARSER:
                self.batch_files = [DBFile(file_path=path) for path in task.batch]  # type: ignore
            case TaskType.CONVERTER:
                for file_id, codec in task.batch.items():  # type: ignore
                    DBFileToConvert.file_id = file_id
                    DBFileToConvert.codec = codec  # type: ignore
                    self.batch_convert.append(
                        DBFileToConvert(file_id=file_id, codec=codec)  # type: ignore
                    )
            case TaskType.PARSER:
                self.batch_files = [DBFile(path=path) for path in task.batch]  # type: ignore
            case TaskType.SORTER:
                self.batch_tracks = [DBTrack(id=track_id) for track_id in task.batch]  # type: ignore

    def get_batch(
        self,
    ) -> List[str | int | Path] | dict[str, ArtType] | dict[int, Codec] | None:
        """Gets the correctly formatted Batch List/Dict."""

        def is_populated_list(list: List[Any]) -> bool:
            return isinstance(list, List) and len(list) > 0

        def get_ids(items: list[Any]):
            return [item.id for item in items]

        def get_paths(files: list[Any]):
            return [file.get_path() for file in files]

        def get_art_batch():
            result = {}
            if is_populated_list(self.batch_albums):
                result.update(
                    {album.mbid: ArtType.ALBUM for album in self.batch_albums}
                )
            if is_populated_list(self.batch_persons):
                result.update(
                    {person.mbid: ArtType.ARTIST for person in self.batch_persons}
                )
            return result if result else None

        def get_codec_batch():
            return (
                {file.file.id: file.codec for file in self.batch_convert}
                if is_populated_list(self.batch_convert)
                else None
            )

        match self.task_type:
            case TaskType.ART_GETTER:
                return get_art_batch()
            case TaskType.CONVERTER:
                return get_codec_batch()  # type: ignore
            case TaskType.TRIMMER | TaskType.PARSER:
                return (
                    get_paths(self.batch_files)
                    if is_populated_list(self.batch_files)
                    else None
                )  # type: ignore
            case TaskType.FINGERPRINTER | TaskType.NORMALIZER | TaskType.EXPORTER:
                return (
                    get_ids(self.batch_files)
                    if is_populated_list(self.batch_files)
                    else None
                )  # type: ignore
            case (
                TaskType.TAGGER
                | TaskType.EXPORTER
                | TaskType.LYRICS_GETTER
                | TaskType.DEDUPER
                | TaskType.SORTER
            ):
                return (
                    get_ids(self.batch_tracks)
                    if is_populated_list(self.batch_tracks)
                    else None
                )  # type: ignore
            case _:
                return None


########################################################################
class ItemBase(SQLModel):
    """base class for item tables"""

    id: int = Field(default=None, primary_key=True, index=True)


class OptFieldBase(SQLModel):
    """base class for optional fields"""

    id: int = Field(default=None, primary_key=True, index=True)


#######################################################################
class DBStat(ItemBase, table=True):
    """Statistics for the application."""

    __tablename__ = "stats"  # type: ignore

    name: str = Field(String(30))
    value: int = Field(default=0)
    range_start: float = Field(default=0)
    range_end: float = Field(default=None)


#######################################################################
class DBFile(ItemBase, table=True):
    """File information."""

    __tablename__ = "files"  # type: ignore

    audio_ip: str = Field(default=None)
    imported: dt.datetime = Field(default=dt.datetime.now(dt.timezone.utc))
    processed: dt.datetime = Field(
        default=None,
        sa_column_kwargs={"onupdate": dt.datetime.now(dt.timezone.utc)},
    )
    bitrate: int = Field(default=None)
    sample_rate: int = Field(default=None)
    channels: int = Field(default=None)
    file_type: str = Field(default=None)
    file_size: int = Field(default=None)
    file_name: str = Field(default=None)
    file_extension: str = Field(default=None)
    codec: StrEnum = Field(StrEnum(Codec), default=Codec.UNKNOWN)  # type: ignore
    length: int = Field(default=None)
    track: DBTrack = Relationship(back_populates="files")
    task: DBTask = Relationship(back_populates="batch_files")
    stage: StrEnum = Field(StrEnum(Stage), default=Stage.NONE)  # type: ignore
    batch_convert: List["DBFileToConvert"] = Relationship(back_populates="file")
    path: str = Field(default=None, sa_column_kwargs={"unique": True})

    def __repr__(self) -> str:
        return f"File {self.id}"

    def get_path(self) -> Path:
        return Path(self.path)


class Track(BaseModel):
    """Operational Track Data class."""

    id: Optional[int] = None
    title: str = ""
    title_sort: str = ""
    subtitle: Optional[str] = ""
    artists: List[int] = []  # List of Person ids
    albums: List[int] = []  # List of Album ids
    key: str = ""
    genres: List[str] = [""]
    fingerprint: str = ""  # get from filedata
    mbid: str = ""
    conductors: List[str] = [""]
    composers: List[str] = [""]
    lyricists: List[str] = [""]
    releasedate: dt.date = dt.date(0000, 0, 0)
    producers: List[str] = [""]
    task: str = ""
    files: List["DBFile"] = Relationship(back_populates="track")

    def __init__(self, track_id: int | None = None) -> None:
        if track_id is not None:
            session = DB().get_session()
            trackdata = session.get_one(DBTrack, id == track_id)
            for key, value in trackdata:
                setattr(self, key, value or None)
            session.close()

    def get_tags(self) -> dict[str, str | int | dt.date]:
        """Gets all the tagdata, converts if nessecary and
        returns it as a dictionairy"""
        result = {}

        result["title"] = self.title
        result["subtitle"] = self.subtitle
        result["artists"] = ",".join(
            map(str, [DBPerson(id=artist_id).full_name for artist_id in self.artists])
        )
        result["albums"] = ",".join(
            map(str, [DBAlbum(id=album_id).title for album_id in self.albums])
        )
        result["key"] = self.key
        result["genres"] = ",".join(map(str, self.genres))
        result["fingerprint"] = self.fingerprint
        result["mbid"] = self.mbid
        result["conductors"] = ",".join(map(str, self.conductors))
        result["composers"] = ",".join(map(str, self.composers))
        result["lyricists"] = ",".join(map(str, self.lyricists))
        result["releasedate"] = self.releasedate
        result["producers"] = ",".join(map(str, self.producers))

        return result

    def get_sortdata(self) -> dict[str, str | int]:
        """Gets all the sortdata, converts if nessecary and returns it as a dictionairy."""
        result = {}
        album_id = self.albums[0]

        result["title_sort"] = self.title_sort
        result["artist_sort"] = (
            DBPerson(id=self.artists[0]).sort_name
            if self.artists
            else "[Unknown Artist]"
        )
        result["album_title_sort"] = (
            DBAlbum(id=album_id).title_sort or "[Unknown Album]"
        )
        result["year"] = str(
            DBAlbum(id=album_id).release_date.year if self.albums else "0000"
        )
        result["disc_number"] = str(
            DBAlbumTrack(album_id=album_id, track_id=self.id).disc_number  # type: ignore
            if self.albums
            else 1
        )
        result["disc_count"] = str(
            DBAlbum(id=album_id).disc_count if self.albums else 1
        )
        result["track_count"] = str(
            DBAlbum(id=album_id).track_count if self.albums else 1
        )
        result["track_number"] = str(
            DBAlbumTrack(album_id=album_id, track_id=self.id).track_number  # type: ignore
            if self.albums
            else 1
        )
        result["bitrate"] = self.files[0].bitrate if self.files else 0
        result["duration"] = self.files[0].length if self.files else 0

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
    mbid: str = Field(default="", sa_type=String, unique=True)
    performers: List["DBPerson"] = Relationship(back_populates="performed_tracks")
    conductors: List["DBPerson"] = Relationship(back_populates="conducted_tracks")
    composers: List["DBPerson"] = Relationship(back_populates="composed_tracks")
    lyricists: List["DBPerson"] = Relationship(back_populates="lyric_tracks")
    producers: List["DBPerson"] = Relationship(back_populates="produced_tracks")
    task: DBTask = Relationship(back_populates="batch_tracks")


class DBAlbum(ItemBase, table=True):
    """Album information."""

    __tablename__ = "albums"  # type: ignore

    disc_count: int = Field(default=0)
    track_count: int = Field(default=0)
    mbid: str = Field(default="", sa_type=String, unique=True)
    title: str = Field(default="")
    title_sort: str = Field(default="")
    subtitle: Optional[str] = Field(default=None)
    release_date: dt.date = Field(
        default=dt.date(0000, 0, 0), sa_column_kwargs={"nullable": False}
    )
    label: "DBLabel" = Relationship(back_populates="albums")
    tracks: List["DBAlbumTrack"] = Relationship(back_populates="albums")
    genres: List["DBGenre"] = Relationship(back_populates="albums")
    artists: List["DBPerson"] = Relationship(back_populates="performed_albums")
    conductors: List["DBPerson"] = Relationship(back_populates="conducted_albums")
    composers: List["DBPerson"] = Relationship(back_populates="composed_albums")
    lyricists: List["DBPerson"] = Relationship(back_populates="lyric_albums")
    producers: List["DBPerson"] = Relationship(back_populates="produced_albums")
    picture: "DBPicture" = Relationship(back_populates="album")
    task: DBTask = Relationship(back_populates="batch_albums")


class DBAlbumTrack(ItemBase, table=True):
    """Album Track information."""

    __tablename__ = "album_tracks"  # type: ignore

    album_id: int = Field(foreign_key="albums.id")
    track_id: int = Field(foreign_key="tracks.id")
    disc_number: int = Field(default=1)
    track_number: int = Field(default=1)
    albums: "DBAlbum" = Relationship(back_populates="tracks")
    tracks: "DBTrack" = Relationship(back_populates="albums")


class DBPerson(ItemBase, table=True):
    """Person information."""

    __tablename__ = "persons"  # type: ignore

    date_of_birth: dt.date = Field(default=None, sa_column_kwargs={"nullable": True})
    date_of_death: Optional[dt.date] = Field(
        default=None, sa_column_kwargs={"nullable": True}
    )
    mbid: str = Field(default="", sa_type=String, unique=True)
    names: List["DBPersonName"] = Relationship(back_populates="person")
    first_name: str = Field(default="")
    middle_name: Optional[str] = Field(default=None)
    last_name: str = Field(default="")
    sort_name: str = Field(default="")
    full_name: str = Field(default="")
    nick_name: Optional[str] = Field(default=None)
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


class DBLabel(ItemBase, table=True):
    """Label information."""

    __tablename__ = "labels"  # type: ignore

    name: str = Field(default="")
    mbid: str = Field(default="", sa_type=String, unique=True)
    albums: List["DBAlbum"] = Relationship(back_populates="label")
    owner: "DBPerson" = Relationship(back_populates="labels")
    parent: "DBLabel" = Relationship(back_populates="children")
    children: List["DBLabel"] = Relationship(back_populates="parent")


class DBKey(ItemBase, table=True):
    """In which key the track is composed."""

    __tablename__ = "keys"  # type: ignore

    key: str
    tracks: List["DBTrack"] = Relationship(back_populates="key")


class DBGenre(ItemBase, table=True):
    """Genre information."""

    __tablename__ = "genres"  # type: ignore

    genre: str = Field(default="")
    tracks: List["DBTrack"] = Relationship(back_populates="genres")
    albums: List["DBAlbum"] = Relationship(back_populates="genres")
    parents: List["DBGenre"] = Relationship(back_populates="children")
    children: List["DBGenre"] = Relationship(back_populates="parents")


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

    date: dt.date
    type: StrEnum = Field(StrEnum(DateType))
    person: "DBPerson" = Relationship(back_populates="dates")
    track: "DBTrack" = Relationship(back_populates="dates")
    album: "DBAlbum" = Relationship(back_populates="dates")


class DBTrackLyric(OptFieldBase, table=True):
    """Track lyrics."""

    __tablename__ = "track_lyrics"  # type: ignore

    Lyric: str
    track: "DBTrack" = Relationship(back_populates="lyric")


class DBTitle(OptFieldBase, table=True):
    """Title information."""

    __tablename__ = "titles"  # type: ignore

    title: str
    title_type: StrEnum = Field(StrEnum(TitleType))
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
    name_type: StrEnum = Field(StrEnum(PersonNameType))
    person: "DBPerson" = Relationship(back_populates="names")
