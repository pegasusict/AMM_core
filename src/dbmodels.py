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
from pathlib import Path
from typing import Any, List, Optional

from pydantic import BaseModel
from sqlmodel import SQLModel, Field, Relationship, String, select
from sqlalchemy.orm import selectinload

from mixins.autofetch import AutoFetchable
from Enums import (
    UserRole,
    TaskType,
    TaskStatus,
    Codec,
    Stage,
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
    role: UserRole = Field(default=UserRole.USER.value)  # Default role is USER
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc),
        sa_column_kwargs={"onupdate": lambda: dt.datetime.now(dt.timezone.utc)},
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, role={self.role})>"


#######################################################################
class DBFileToConvert(AutoFetchable, SQLModel, table=True):
    """DB Model for files to convert."""

    __tablename__ = "files_to_convert"  # type: ignore

    file: "DBFile" = Relationship(back_populates="batch_convert")
    codec: Codec = Field(default=Codec.UNKNOWN)  # type: ignore
    task: "DBTask" = Relationship(back_populates="batch_convert")

    def __repr__(self) -> str:
        return f"<DBFileToConvert(file_id={self.file.id}, codec={self.codec})>"


class DBTask(AutoFetchable, SQLModel, table=True):
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
    batch_labels: List["DBLabel"] = Relationship(back_populates="task")
    batch_convert: List["DBFileToConvert"] = Relationship(back_populates="task")
    processed: int = Field(default=0, sa_type=int)
    progress: float = Field(default=0, sa_type=float)
    function: str = Field(default="", sa_type=String)
    kwargs: str = Field(default="", sa_type=String)
    result: str = Field(default="", sa_type=String)
    error: str = Field(default="", sa_type=String)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    task_type: TaskType = Field(default=TaskType.CUSTOM)

    def __repr__(self) -> str:
        return f"<DBTask(id={self.id}, task_id={self.task_id}, status={self.status})>"

    required_fields = (
        "task_id",
        "start_time",
        "end_time",
        "duration",
        "processed",
        "progress",
        "function",
        "result",
        "error",
        "status",
        "task_type",
    )

    def import_task(self, task: Task) -> None:
        """Imports a task into the database."""
        self._fill_required_fields(task)

        # Dispatch table for handlers
        task_handlers = {
            TaskType.ART_GETTER: self._handle_art_getter,
            TaskType.CONVERTER: self._handle_converter,
        }

        if task.task_type in task_handlers:
            task_handlers[task.task_type](task)
            return

        if task.task_type in self._track_tasks():
            self._handle_track_task(task)
        elif task.task_type in self._file_id_tasks():
            self._handle_file_id_task(task)
        elif task.task_type in self._file_path_tasks():
            self._handle_file_path_task(task)

    # ---------------------------
    # Private Helper Methods
    # ---------------------------

    def _fill_required_fields(self, task: Task) -> None:
        for field in self.required_fields:
            if not hasattr(self, field) or getattr(self, field) in (None, "", []):
                raise ValueError(f"Task is missing required attribute: {field}")
            setattr(self, field, getattr(task, field))

    def _handle_art_getter(self, task: Task) -> None:
        albums = []
        persons = []
        labels = []
        for mbid, art_type in task.batch:  # type: ignore
            if art_type not in ArtType:
                raise InvalidValueError(f"Invalid art type: {art_type}")
            if art_type == ArtType.ALBUM:
                albums.append(DBAlbum(mbid=mbid))
            elif art_type == ArtType.LABEL:
                labels.append(DBLabel(mbid=mbid))
            else:
                persons.append(DBPerson(mbid=mbid))
        self.batch_albums = albums or None  # type: ignore
        self.batch_persons = persons or None  # type: ignore
        self.batch_labels = labels or None  # type: ignore

    def _handle_converter(self, task: Task) -> None:
        self.batch_convert = [
            DBFileToConvert(file_id=file_id, codec=codec)  # type: ignore
            for file_id, codec in task.batch.items()  # type: ignore
        ]

    def _handle_track_task(self, task: Task) -> None:
        self.batch_tracks = [
            DBTrack(id=track_id)  # type: ignore
            for track_id in task.batch  # type: ignore
        ]

    def _handle_file_id_task(self, task: Task) -> None:
        self.batch_files = [
            DBFile(id=file_id)  # type: ignore
            for file_id in task.batch  # type: ignore
        ]

    def _handle_file_path_task(self, task: Task) -> None:
        self.batch_files = [
            DBFile(file_path=path)  # type: ignore
            for path in task.batch  # type: ignore
        ]

    # ---------------------------
    # Static Task Type Groups
    # ---------------------------

    @staticmethod
    def _track_tasks() -> set:
        return {
            TaskType.TAGGER,
            TaskType.LYRICS_GETTER,
            TaskType.DEDUPER,
            TaskType.SORTER,
        }

    @staticmethod
    def _file_id_tasks() -> set:
        return {
            TaskType.FINGERPRINTER,
            TaskType.EXPORTER,
            TaskType.NORMALIZER,
        }

    @staticmethod
    def _file_path_tasks() -> set:
        return {
            TaskType.TRIMMER,
            TaskType.PARSER,
        }

    def get_batch(
        self,
    ) -> List[str] | List[int] | List[Path] | dict[str, ArtType] | dict[int, Codec] | None:
        """Gets the correctly formatted Batch List/Dict."""

        def is_populated_list(subject: List[Any]) -> bool:
            return isinstance(subject, List) and len(subject) > 0

        def get_ids(items: list[Any]):
            return [item.id for item in items]

        def get_paths(files: list[Any]):
            return [file.get_path() for file in files]

        def get_art_batch():
            result = {}
            if is_populated_list(self.batch_albums):
                result.update({album.mbid: ArtType.ALBUM for album in self.batch_albums})
            if is_populated_list(self.batch_persons):
                result.update({person.mbid: ArtType.ARTIST for person in self.batch_persons})
            return result if result else None

        def get_codec_batch():
            return {file.file.id: file.codec for file in self.batch_convert} if is_populated_list(self.batch_convert) else None

        match self.task_type:
            case TaskType.ART_GETTER:
                return get_art_batch()
            case TaskType.CONVERTER:
                return get_codec_batch()  # type: ignore
            case TaskType.TRIMMER | TaskType.PARSER:
                return get_paths(self.batch_files) if is_populated_list(self.batch_files) else None  # type: ignore
            case TaskType.FINGERPRINTER | TaskType.NORMALIZER | TaskType.EXPORTER:
                return get_ids(self.batch_files) if is_populated_list(self.batch_files) else None  # type: ignore
            case TaskType.TAGGER | TaskType.EXPORTER | TaskType.LYRICS_GETTER | TaskType.DEDUPER | TaskType.SORTER:
                return get_ids(self.batch_tracks) if is_populated_list(self.batch_tracks) else None  # type: ignore
            case _:
                return None


########################################################################
class ItemBase(AutoFetchable, SQLModel):
    """base class for item tables"""

    id: int = Field(default=None, primary_key=True, index=True)


class OptFieldBase(SQLModel):
    """base class for optional fields"""

    id: int = Field(default=None, primary_key=True, index=True)


#######################################################################
class DBStat(ItemBase, table=True):
    """Statistics for the application."""

    __tablename__ = "stats"  # type: ignore

    name: str = Field(default="", sa_type=String)
    value: int = Field(default=0)
    range_start: float = Field(default=0)
    range_end: float = Field(default=None)
    unit: str = Field(default="", sa_type=String)


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
    codec: Codec = Field(default=Codec.UNKNOWN)
    duration: int = Field(default=None)
    track: DBTrack = Relationship(back_populates="files")
    track_id: int = Field(foreign_key="tracks.id")
    task: DBTask = Relationship(back_populates="batch_files")
    task_id: int = Field(foreign_key="tasks.id")
    stage: Stage = Field(default=Stage.NONE)
    batch_convert: "DBFileToConvert" = Relationship(back_populates="file")
    batch_id: int = Field(foreign_key="filestoconvert.id")
    file_path: str = Field(default=None, sa_column_kwargs={"unique": True})


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
    mbid: str = ""
    conductors: List[str] = [""]
    composers: List[str] = [""]
    lyricists: List[str] = [""]
    releasedate: dt.date = dt.date(0000, 1, 1)
    producers: List[str] = [""]
    task: str = ""
    files: List["DBFile"] = []  # List of File ids

    def __init__(self, track_id: int | None = None) -> None:
        if track_id is not None:
            session = DB().get_session()
            trackdata = session.exec(
                select(DBTrack)
                .where(DBTrack.id == track_id)
                .options(
                    selectinload(DBTrack.albums),  # type: ignore
                    selectinload(DBTrack.files),  # type: ignore
                    selectinload(DBTrack.artists),  # type: ignore
                    selectinload(DBTrack.album_tracks),  # type: ignore
                    # Add more as needed
                )
            ).first()
            session.close()
            if not trackdata:
                raise InvalidValueError(f"Track with id {track_id} not found in the database.")
            for key, value in trackdata.__dict__.items():
                setattr(self, key, value or None)

    def get_tags(self) -> dict[str, str | int | dt.date]:
        """Gets all the tagdata, converts if nessecary and
        returns it as a dictionairy"""
        result = {}

        result["title"] = self.title
        result["subtitle"] = self.subtitle
        result["artists"] = ",".join(map(str, [DBPerson(id=artist_id).full_name for artist_id in self.artists]))
        result["albums"] = ",".join(map(str, [DBAlbum(id=album_id).title for album_id in self.albums]))
        result["key"] = self.key
        result["genres"] = ",".join(map(str, self.genres))
        result["mbid"] = self.mbid
        result["conductors"] = ",".join(map(str, self.conductors))
        result["composers"] = ",".join(map(str, self.composers))
        result["lyricists"] = ",".join(map(str, self.lyricists))
        result["releasedate"] = self.releasedate
        result["producers"] = ",".join(map(str, self.producers))

        return result

    def get_sortdata(self) -> dict[str, str | int]:
        """Gets all the sortdata, converts if necessary and returns it as a dictionary."""

        album = self._get_album()
        artist = self._get_artist()
        album_track = self._get_album_track(album.id) if album else None
        file = self.files[0] if self.files else None

        def safe(attr: Any, default: Any = "") -> Any:
            return attr if attr is not None else default

        return {
            "title_sort": self.title_sort,
            "artist_sort": safe(getattr(artist, "sort_name", None), "[Unknown Artist]"),
            "album_title_sort": safe(getattr(album, "title_sort", None), "[Unknown Album]"),
            "year": str(safe(getattr(album, "release_date", None), "0000").year if album else "0000"),
            "disc_number": str(safe(getattr(album_track, "disc_number", None), 1)),
            "disc_count": str(safe(getattr(album, "disc_count", None), 1)),
            "track_count": str(safe(getattr(album, "track_count", None), 1)),
            "track_number": str(safe(getattr(album_track, "track_number", None), 1)),
            "bitrate": safe(getattr(file, "bitrate", None), 0),
            "duration": safe(getattr(file, "length", None), 0),
        }

    def _get_album(self) -> DBAlbum | None:
        if not self.albums:
            return None
        return DBAlbum(id=self.albums[0])

    def _get_album_track(self, album_id: int) -> DBAlbumTrack | None:
        if not self.id:
            return None
        return DBAlbumTrack(album_id=album_id, track_id=self.id)  # type: ignore

    def _get_artist(self) -> DBPerson | None:
        if not self.artists:
            return None
        return DBPerson(id=self.artists[0])


class DBTrack(ItemBase, table=True):
    """Track information."""

    __tablename__ = "tracks"  # type: ignore

    composed: dt.date = Field(default=dt.date(0000, 1, 1), sa_column_kwargs={"nullable": False})
    release_date: dt.date = Field(default=dt.date(0000, 1, 1), sa_column_kwargs={"nullable": False})
    title: str = Field(default="")
    title_sort: str = Field(default="")
    subtitle: Optional[str] = Field(default=None)
    files: List["DBFile"] = Relationship(back_populates="track")
    album_tracks: List["DBAlbumTrack"] = Relationship(back_populates="track")
    key: "DBKey" = Relationship(back_populates="tracks")
    genres: List["DBGenre"] = Relationship(back_populates="tracks")
    mbid: str = Field(default="", sa_type=String, unique=True)
    performers: List["DBPerson"] = Relationship(back_populates="performed_tracks")
    conductors: List["DBPerson"] = Relationship(back_populates="conducted_tracks")
    composers: List["DBPerson"] = Relationship(back_populates="composed_tracks")
    lyricists: List["DBPerson"] = Relationship(back_populates="lyric_tracks")
    producers: List["DBPerson"] = Relationship(back_populates="produced_tracks")
    task: DBTask = Relationship(back_populates="batch_tracks")
    lyric: "DBTrackLyric" = Relationship(back_populates="track")


class DBAlbum(ItemBase, table=True):
    """Album information."""

    __tablename__ = "albums"  # type: ignore

    mbid: str = Field(default="", sa_type=String, unique=True)
    title: str = Field(default="")
    title_sort: str = Field(default="")
    subtitle: Optional[str] = Field(default=None)
    release_date: dt.date = Field(default=dt.date(0000, 1, 1), sa_column_kwargs={"nullable": False})
    release_country: str = Field(default="")
    label: "DBLabel" = Relationship(back_populates="albums")
    album_tracks: List["DBAlbumTrack"] = Relationship(back_populates="album")
    genres: List["DBGenre"] = Relationship(back_populates="albums")
    artists: List["DBPerson"] = Relationship(back_populates="performed_albums")
    conductors: List["DBPerson"] = Relationship(back_populates="conducted_albums")
    composers: List["DBPerson"] = Relationship(back_populates="composed_albums")
    lyricists: List["DBPerson"] = Relationship(back_populates="lyric_albums")
    producers: List["DBPerson"] = Relationship(back_populates="produced_albums")
    picture: "DBPicture" = Relationship(back_populates="album")
    disc_count: int = Field(default=0)
    track_count: int = Field(default=0)
    task: DBTask = Relationship(back_populates="batch_albums")
    task_id: int = Field(default=None, foreign_key="tasks.id")


class DBAlbumTrack(ItemBase, table=True):
    """Album Track information."""

    __tablename__ = "album_tracks"  # type: ignore

    album_id: int = Field(foreign_key="albums.id")
    track_id: int = Field(foreign_key="tracks.id")
    disc_number: int = Field(default=1)
    track_number: int = Field(default=1)
    album: "DBAlbum" = Relationship(back_populates="album_tracks")
    track: "DBTrack" = Relationship(back_populates="album_tracks")


class DBPerson(ItemBase, table=True):
    """Person information."""

    __tablename__ = "persons"  # type: ignore

    mbid: str = Field(default="", sa_type=String, unique=True)
    first_name: str = Field(default="")
    middle_name: Optional[str] = Field(default=None)
    last_name: str = Field(default="")
    sort_name: str = Field(default="")
    full_name: str = Field(default="")
    nick_name: Optional[str] = Field(default=None)
    alias: Optional[str] = Field(default=None)
    date_of_birth: dt.date = Field(default=None, sa_column_kwargs={"nullable": True})
    date_of_death: Optional[dt.date] = Field(default=None, sa_column_kwargs={"nullable": True})
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
    labels: List["DBLabel"] = Relationship(back_populates="owner")


class DBLabel(ItemBase, table=True):
    """Label information."""

    __tablename__ = "labels"  # type: ignore

    name: str = Field(default="")
    mbid: str = Field(default="", sa_type=String, unique=True)
    founded: dt.date = Field(default=None, sa_column_kwargs={"nullable": True})
    defunct: Optional[dt.date] = Field(default=None, sa_column_kwargs={"nullable": True})
    description: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})
    picture: "DBPicture" = Relationship(back_populates="label")
    albums: List["DBAlbum"] = Relationship(back_populates="label")
    owner: "DBPerson" = Relationship(back_populates="labels")
    owner_id: int = Field(default=None, foreign_key="persons.id")
    parent: "DBLabel" = Relationship(back_populates="children")
    children: List["DBLabel"] = Relationship(back_populates="parent")
    parent_id: Optional[int] = Field(default=None, foreign_key="labels.id")


class DBKey(ItemBase, table=True):
    """In which key the track is composed."""

    __tablename__ = "keys"  # type: ignore

    key: str
    tracks: List["DBTrack"] = Relationship(back_populates="key")


class DBGenre(ItemBase, table=True):
    """Genre information."""

    __tablename__ = "genres"  # type: ignore

    genre: str = Field(default="")
    description: str = Field(default="")
    tracks: List["DBTrack"] = Relationship(back_populates="genres")
    albums: List["DBAlbum"] = Relationship(back_populates="genres")
    parents: List["DBGenre"] = Relationship(back_populates="children")
    children: List["DBGenre"] = Relationship(back_populates="parents")


#######################################################################
class DBTrackLyric(OptFieldBase, table=True):
    """Track lyrics."""

    __tablename__ = "track_lyrics"  # type: ignore

    lyric: str
    track: "DBTrack" = Relationship(back_populates="lyric")


class DBPicture(OptFieldBase, table=True):
    """Album/Person Pictures"""

    __tablename__ = "pictures"  # type: ignore

    picture_path: str = Field(unique=True)
    album: "DBAlbum" = Relationship(back_populates="picture")
    person: "DBPerson" = Relationship(back_populates="picture")
    label: "DBLabel" = Relationship(back_populates="picture")
