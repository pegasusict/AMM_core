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
from typing import Optional, List, Any
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import JSON, String

from mixins.autofetch import AutoFetchable
from enums import (
    UserRole,
    TaskType,
    TaskStatus,
    Codec,
    ArtType,
)
from .exceptions import InvalidValueError
from .Tasks import Task


class DBUser(AutoFetchable, SQLModel, table=True):
    """User model."""

    __tablename__ = "users"  # type: ignore

    id: Optional[int] = Field(primary_key=True, index=True, default=None)
    username: str = Field(unique=True, default="", sa_type=String, max_length=40)
    email: str = Field(unique=True, default="", sa_type=String, max_length=255)
    password_hash: str = Field(default="", sa_type=String, max_length=255)
    first_name: str = Field(default="", sa_type=String, max_length=40)
    middle_name: str = Field(default="", sa_type=String, max_length=16)
    last_name: str = Field(default="", sa_type=String, max_length=40)
    date_of_birth: dt.datetime = Field(default=None)
    is_active: bool = Field(default=True)
    role: UserRole = Field(default=UserRole.USER.value)  # Default role is USER
    created_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    updated_at: dt.datetime = Field(
        default_factory=lambda: dt.datetime.now(dt.timezone.utc),
        sa_column_kwargs={"onupdate": lambda: dt.datetime.now(dt.timezone.utc)},
    )

    queue: Optional["DBQueue"] = Relationship(back_populates="user")
    playlists: List["DBPlaylist"] = Relationship(back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, role={self.role})>"


class DBQueue(AutoFetchable, SQLModel, table=True):
    __tablename__ = "user_queues"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    track_ids: List[int] = Field(default=[], sa_column_kwargs={"type_": JSON})

    user: DBUser = Relationship(back_populates="queue")


class DBPlaylist(AutoFetchable, SQLModel, table=True):
    __tablename__ = "playlists"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_type=String, max_length=255)
    user_id: int = Field(foreign_key="users.id", nullable=False)

    user: DBUser = Relationship(back_populates="playlists")
    tracks: List["DBPlaylistTrack"] = Relationship(back_populates="playlist")


class DBPlaylistTrack(AutoFetchable, SQLModel, table=True):
    __tablename__ = "playlist_tracks"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(foreign_key="playlists.id", nullable=False)
    track_id: int = Field(foreign_key="tracks.id", nullable=False)
    position: int = Field(default=0)

    playlist: DBPlaylist = Relationship(back_populates="tracks")
    track: "DBTrack" = Relationship()


#######################################################################
class DBFileToConvert(AutoFetchable, SQLModel, table=True):
    """DB Model for files to convert."""

    __tablename__ = "files_to_convert"  # type: ignore

    codec: Codec = Field(default=Codec.UNKNOWN)
    file_id: int = Field(foreign_key="files.id")
    task_id: int = Field(foreign_key="tasks.id")

    file: "DBFile" = Relationship(back_populates="batch_convert")
    task: "DBTask" = Relationship(back_populates="batch_convert")

    def __repr__(self) -> str:
        return f"<DBFileToConvert(file_id={self.file_id}, codec={self.codec})>"


class DBTask(AutoFetchable, SQLModel, table=True):
    """DB Model for Task."""

    __tablename__ = "tasks"  # type: ignore

    id: int = Field(default=None, sa_type=int, primary_key=True, unique=True)
    task_id: str = Field(default="", nullable=False, sa_type=String, max_length=40)
    start_time: dt.datetime = Field(default=None)
    end_time: dt.datetime = Field(default=None)
    duration: int = Field(default=0, sa_type=int)
    processed: int = Field(default=0, sa_type=int)
    progress: float = Field(default=0, sa_type=float)
    function: str = Field(default="", sa_type=String, max_length=20)
    kwargs: str = Field(default="", sa_type=String, max_length=1024)
    result: str = Field(default="", sa_type=String, max_length=1024)
    error: str = Field(default="", sa_type=String, max_length=1024)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    task_type: TaskType = Field(default=TaskType.CUSTOM)

    batch_files: List["DBFile"] = Relationship(back_populates="task")
    batch_tracks: List["DBTrack"] = Relationship(back_populates="task")
    batch_albums: List["DBAlbum"] = Relationship(back_populates="task")
    batch_persons: List["DBPerson"] = Relationship(back_populates="task")
    batch_labels: List["DBLabel"] = Relationship(back_populates="task")
    batch_convert: List["DBFileToConvert"] = Relationship(back_populates="task")

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
        elif task.task_type in self._file_dict_tasks():
            self._handle_file_dict_task(task)

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

    def _handle_file_dict_task(self, task: Task) -> None:
        self.batch_files = [
            DBFile(id=int(file_id))
            for file_id, _ in task.batch  # type: ignore
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
    def _file_dict_tasks() -> set:
        return {
            TaskType.TRIMMER,
            TaskType.PARSER,
        }

    def get_batch(
        self,
    ) -> list[str] | list[int] | list[Path] | dict[str, ArtType] | dict[int, Codec] | None:
        """Gets the correctly formatted Batch List/Dict."""

        def is_populated_list(subject: list[Any]) -> bool:
            return isinstance(subject, list) and len(subject) > 0

        def get_ids(items: list[Any]):
            return [item.id for item in items]

        def get_art_batch():
            result = {}
            if is_populated_list(self.batch_albums):
                result.update({album.mbid: ArtType.ALBUM for album in self.batch_albums})
            if is_populated_list(self.batch_persons):
                result.update({person.mbid: ArtType.ARTIST for person in self.batch_persons})
            if is_populated_list(self.batch_labels):
                result.update({label.mbid: ArtType.LABEL for label in self.batch_labels})
            return result or None

        def get_codec_batch():
            return {file.file.id: file.codec for file in self.batch_convert} if is_populated_list(self.batch_convert) else None

        match self.task_type:
            case TaskType.ART_GETTER:
                return get_art_batch()
            case TaskType.CONVERTER:
                return get_codec_batch()  # type: ignore
            case TaskType.FINGERPRINTER | TaskType.NORMALIZER | TaskType.EXPORTER | TaskType.TRIMMER | TaskType.PARSER:
                return get_ids(self.batch_files) if is_populated_list(self.batch_files) else None  # type: ignore
            case TaskType.TAGGER | TaskType.EXPORTER | TaskType.LYRICS_GETTER | TaskType.DEDUPER | TaskType.SORTER:
                return get_ids(self.batch_tracks) if is_populated_list(self.batch_tracks) else None  # type: ignore
            case _:
                return None


class DBTaskStat(SQLModel, table=True):
    __tablename__ = "task_stats"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    task_type: TaskType = Field(index=True)

    last_run: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))

    imported: int = Field(default=0)
    parsed: int = Field(default=0)
    trimmed: int = Field(default=0)
    deduped: int = Field(default=0)

    total_playtime: int = Field(default=0)  # in seconds
    average_playtime: int = Field(default=0)
    total_filesize: int = Field(default=0)  # in bytes
    average_filesize: int = Field(default=0)

    updated_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))


class DBTaskStatSnapshot(SQLModel, table=True):
    __tablename__ = "task_stat_snapshots"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    task_type: TaskType = Field(index=True)
    snapshot_time: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))

    total_playtime: int = 0
    total_filesize: int = 0
    imported: int = 0
    parsed: int = 0
    trimmed: int = 0
    deduped: int = 0


########################################################################
class ItemBase(AutoFetchable, SQLModel):
    """base class for item tables"""

    id: int = Field(default=None, primary_key=True, index=True)


class OptFieldBase(AutoFetchable, SQLModel):
    """base class for optional fields"""

    id: int = Field(default=None, primary_key=True, index=True)


#######################################################################
class DBStat(ItemBase, table=True):
    """Statistics for the application."""

    __tablename__ = "stats"  # type: ignore

    name: str = Field(default="", sa_type=String, max_length=40)
    value: int = Field(default=0)
    range_start: float = Field(default=0)
    range_end: float = Field(default=None)
    unit: str = Field(default="", sa_type=String, max_length=16)


#######################################################################
class DBFile(ItemBase, table=True):
    """File information."""

    __tablename__ = "files"  # type: ignore

    audio_ip: str = Field(default=None, sa_type=String, max_length=1024)
    imported: dt.datetime = Field(default=dt.datetime.now(dt.timezone.utc))
    processed: dt.datetime = Field(
        default=None,
        sa_column_kwargs={"onupdate": dt.datetime.now(dt.timezone.utc)},
    )
    bitrate: int = Field(default=None)
    sample_rate: int = Field(default=None)
    channels: int = Field(default=None)
    file_type: str = Field(default=None, sa_type=String, max_length=20)
    file_size: int = Field(default=None)
    file_name: str = Field(default=None, sa_type=String, max_length=255)
    file_extension: str = Field(default=None, sa_type=String, max_length=16)
    codec: Codec = Field(default=Codec.UNKNOWN)
    duration: int = Field(default=None)
    track_id: int = Field(default=None, foreign_key="tracks.id")
    task_id: int = Field(default=None, foreign_key="tasks.id")
    batch_id: int = Field(default=None, foreign_key="filestoconvert.id")
    file_path: str = Field(default=None, sa_column_kwargs={"unique": True}, sa_type=String, max_length=1024)
    # --- 🔹 Stage/Substage Record ---
    stage: Optional[int] = Field(default=0)  # Holds top-level stage value (e.g. 1, 2, 4, etc)
    substages: Optional[List[str]] = Field(default_factory=list, sa_type=str)  # JSON-encoded list
    stage_completed: bool = Field(default=False)

    track: DBTrack = Relationship(back_populates="files")
    task: DBTask = Relationship(back_populates="batch_files")
    batch_convert: "DBFileToConvert" = Relationship(back_populates="file")

    def add_completed_substage(self, parent: str, substage: str):
        subs = self.stages.get(parent, [])
        if substage not in subs:
            subs.append(substage)
            self.stages[parent] = subs

    def mark_stage_completed(self, stage: str):
        self.stages[stage] = []
        self.processed = dt.datetime.now(dt.timezone.utc)


class DBTrack(ItemBase, table=True):
    """Track information."""

    __tablename__ = "tracks"  # type: ignore

    composed: dt.date = Field(default=dt.date.min, sa_column_kwargs={"nullable": False})
    release_date: dt.date = Field(default=dt.date.min, sa_column_kwargs={"nullable": False})
    title: str = Field(default="", sa_type=String, max_length=255)
    title_sort: str = Field(default="", sa_type=String, max_length=255)
    subtitle: Optional[str] = Field(default=None)
    mbid: str = Field(default="", sa_type=String, unique=True, max_length=40)

    files: List["DBFile"] = Relationship(back_populates="track")
    album_tracks: List["DBAlbumTrack"] = Relationship(back_populates="track")
    key: "DBKey" = Relationship(back_populates="tracks")
    genres: List["DBGenre"] = Relationship(back_populates="tracks")
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

    mbid: str = Field(default="", sa_type=String, unique=True, max_length=40)
    title: str = Field(default="")
    title_sort: str = Field(default="")
    subtitle: Optional[str] = Field(default=None)
    release_date: dt.date = Field(default=dt.date.min, sa_column_kwargs={"nullable": False})
    release_country: str = Field(default="")
    disc_count: int = Field(default=0)
    track_count: int = Field(default=0)
    task_id: int = Field(default=None, foreign_key="tasks.id")

    task: "DBTask" = Relationship(back_populates="batch_albums")
    label: "DBLabel" = Relationship(back_populates="albums")
    album_tracks: List["DBAlbumTrack"] = Relationship(back_populates="album")
    genres: List["DBGenre"] = Relationship(back_populates="albums")
    artists: List["DBPerson"] = Relationship(back_populates="performed_albums")
    conductors: List["DBPerson"] = Relationship(back_populates="conducted_albums")
    composers: List["DBPerson"] = Relationship(back_populates="composed_albums")
    lyricists: List["DBPerson"] = Relationship(back_populates="lyric_albums")
    producers: List["DBPerson"] = Relationship(back_populates="produced_albums")
    picture: "DBPicture" = Relationship(back_populates="album")


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

    mbid: str = Field(default="", sa_type=String, unique=True, max_length=40)
    first_name: str = Field(default="", sa_type=String, max_length=64)
    middle_name: Optional[str] = Field(default=None, sa_type=String, max_length=16)
    last_name: str = Field(default="", sa_type=String, max_length=64)
    sort_name: str = Field(default="", sa_type=String, max_length=255)
    full_name: str = Field(default="", sa_type=String, max_length=255)
    nick_name: Optional[str] = Field(default=None, sa_type=String, max_length=255)
    alias: Optional[str] = Field(default=None, sa_type=String, max_length=255)
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

    name: str = Field(default="", sa_type=String, max_length=255)
    mbid: str = Field(default="", sa_type=String, unique=True, max_length=40)
    founded: dt.date = Field(default=None, sa_column_kwargs={"nullable": True})
    defunct: Optional[dt.date] = Field(default=None, sa_column_kwargs={"nullable": True})
    description: Optional[str] = Field(
        default=None,
        sa_column_kwargs={"nullable": True},
        sa_type=String,
        max_length=1024,
    )

    owner_id: int = Field(default=None, foreign_key="persons.id")
    parent_id: Optional[int] = Field(default=None, foreign_key="labels.id")

    parent: "DBLabel" = Relationship(back_populates="children")
    children: List["DBLabel"] = Relationship(back_populates="parent")
    picture: "DBPicture" = Relationship(back_populates="label")
    albums: List["DBAlbum"] = Relationship(back_populates="label")
    owner: "DBPerson" = Relationship(back_populates="labels")


class DBKey(ItemBase, table=True):
    """In which key the track is composed."""

    __tablename__ = "keys"  # type: ignore

    key: str = Field(sa_type=String, max_length=16, unique=True, nullable=False)

    tracks: List["DBTrack"] = Relationship(back_populates="key")


class DBGenre(ItemBase, table=True):
    """Genre information."""

    __tablename__ = "genres"  # type: ignore

    genre: str = Field(default="", sa_type=String, max_length=64)
    description: str = Field(default="", sa_type=String, max_length=1024)

    tracks: List["DBTrack"] = Relationship(back_populates="genres")
    albums: List["DBAlbum"] = Relationship(back_populates="genres")
    parents: List["DBGenre"] = Relationship(back_populates="children")
    children: List["DBGenre"] = Relationship(back_populates="parents")


#######################################################################
class DBTrackLyric(OptFieldBase, table=True):
    """Track lyrics."""

    __tablename__ = "track_lyrics"  # type: ignore

    lyric: str = Field(sa_type=String, max_length=2048)

    track: "DBTrack" = Relationship(back_populates="lyric")


class DBPicture(OptFieldBase, table=True):
    """Album/Person Pictures"""

    __tablename__ = "pictures"  # type: ignore

    picture_path: Path = Field(unique=True, sa_type=String, max_length=1024)

    album: "DBAlbum" = Relationship(back_populates="picture")
    person: "DBPerson" = Relationship(back_populates="picture")
    label: "DBLabel" = Relationship(back_populates="picture")
