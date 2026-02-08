#  Copyleft 2021-2026 Mattijs Snepvangers.
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

"""Contains the GraphQL schemas."""

from __future__ import annotations
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Generic, List, Optional, TypeVar

import strawberry
from pydantic import EmailStr

from Enums import Stage, TaskType, UserRole, Codec


# ----------------- User & Task -----------------


@strawberry.type()
class User:
    id: Optional[int] = None
    username: Optional[str] = None
    password_hash: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: Optional[bool] = None


@strawberry.type()
class Task:
    id: Optional[int] = None
    task_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    batch_files: Optional[List[int]] = None
    batch_tracks: Optional[List[int]] = None
    batch_albums: Optional[List[int]] = None
    batch_persons: Optional[List[int]] = None
    batch_labels: Optional[List[int]] = None
    batch_convert: Optional[List[int]] = None
    processed: Optional[int] = None
    progress: Optional[int] = None
    function: Optional[str] = None
    kwargs: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    status: Optional[str] = None
    task_type: Optional[str] = None


@strawberry.type()
class DisplayTask:
    task_id: Optional[str]
    task_type: Optional[str]
    progress: Optional[int]
    start_time: Optional[datetime]
    status: Optional[str]


@strawberry.type()
class Stat:
    id: Optional[int] = None
    name: Optional[str] = None
    value: Optional[float] = None
    range_start: Optional[float] = None
    range_end: Optional[float] = None
    unit: Optional[str] = None


# ----------------- Core Metadata Types -----------------


@strawberry.type()
class File:
    id: Optional[int] = None
    imported: Optional[datetime] = None
    processed: Optional[datetime] = None
    file_path: Optional[Path] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_extension: Optional[str] = None
    size: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    codec: Optional[Codec] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    duration: Optional[int] = None
    stage: Optional[Stage] = None
    fingerprint: Optional[str] = None
    track_id: Optional[int] = None
    task_id: Optional[int] = None
    batch_id: Optional[int] = None


@strawberry.type()
class Track:
    id: Optional[int] = None
    title: Optional[str] = None
    title_sort: Optional[str] = None
    subtitle: Optional[str] = None
    artists: Optional[List[int]] = None
    albums: Optional[List[int]] = None
    key: Optional[str] = None
    genres: Optional[List[int]] = None
    mbid: Optional[str] = None
    conductors: Optional[List[int]] = None
    composers: Optional[List[int]] = None
    lyricists: Optional[List[int]] = None
    producers: Optional[List[int]] = None
    releasedate: Optional[date] = None
    lyrics: Optional[str] = None
    files: Optional[List[int]] = None
    task_id: Optional[int] = None


@strawberry.type()
class Album:
    id: Optional[int] = None
    mbid: Optional[str] = None
    title: Optional[str] = None
    title_sort: Optional[str] = None
    subtitle: Optional[str] = None
    releasedate: Optional[date] = None
    release_country: Optional[str] = None
    label: Optional[str] = None
    tracks: Optional[List[int]] = None
    genres: Optional[List[int]] = None
    artists: Optional[List[int]] = None
    conductors: Optional[List[int]] = None
    composers: Optional[List[int]] = None
    lyricists: Optional[List[int]] = None
    producers: Optional[List[int]] = None
    picture: Optional[Path] = None
    disc_count: Optional[int] = None
    track_count: Optional[int] = None
    task_id: Optional[int] = None


@strawberry.type()
class Genre:
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    albums: Optional[List[int]] = None
    tracks: Optional[List[int]] = None
    parents: Optional[List[int]] = None
    children: Optional[List[int]] = None


@strawberry.type()
class Person:
    id: Optional[int] = None
    mbid: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    alias: Optional[str] = None
    nick_name: Optional[str] = None
    sort_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    picture: Optional[Path] = None
    performed_tracks: Optional[List[int]] = None
    conducted_tracks: Optional[List[int]] = None
    composed_tracks: Optional[List[int]] = None
    lyric_tracks: Optional[List[int]] = None
    produced_tracks: Optional[List[int]] = None
    performed_albums: Optional[List[int]] = None
    conducted_albums: Optional[List[int]] = None
    composed_albums: Optional[List[int]] = None
    lyric_albums: Optional[List[int]] = None
    produced_albums: Optional[List[int]] = None
    task_id: Optional[int] = None
    labels: Optional[List[int]] = None


@strawberry.type()
class Label:
    id: Optional[int] = None
    name: Optional[str] = None
    mbid: Optional[str] = None
    description: Optional[str] = None
    founded: Optional[date] = None
    defunct: Optional[date] = None
    albums: Optional[List[int]] = None
    picture: Optional[Path] = None
    parent: Optional[int] = None
    children: Optional[List[int]] = None
    owner: Optional[int] = None


@strawberry.type()
class Key:
    id: Optional[int] = None
    name: Optional[str] = None
    tracks: Optional[List[int]] = None


# ----------------- PlayerService + Playlist/Queue -----------------


@strawberry.type
class PlayerTrack:
    id: int
    title: str
    subtitle: Optional[str]
    artists: List[str]
    album_picture: Optional[str]  # URL or static path
    duration_seconds: Optional[int]
    lyrics: Optional[str] = None


@strawberry.type
class PlayerStatus:
    current_track: Optional[PlayerTrack]
    is_playing: bool


@strawberry.type
class Playlist:
    id: int
    name: str
    track_ids: List[int]


@strawberry.type
class Queue:
    track_ids: List[int]


@strawberry.type
class AuthPayload:
    access_token: str
    refresh_token: str
    user: User


# ----------------- Mutation Input Types -----------------


@strawberry.input
class UserCreateInput:
    username: str
    email: EmailStr
    password_hash: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


@strawberry.input
class UserUpdateInput:
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password_hash: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


@strawberry.input
class TrackInput:
    title: Optional[str] = None
    mbid: Optional[str] = None


@strawberry.input
class AlbumInput:
    title: Optional[str] = None


@strawberry.input
class PersonInput:
    full_name: Optional[str] = None


@strawberry.input
class GenreInput:
    name: Optional[str] = None


@strawberry.input
class LabelInput:
    name: Optional[str] = None
    mbid: Optional[str] = None
    description: Optional[str] = None
    founded: Optional[date] = None
    defunct: Optional[date] = None
    owner_id: Optional[int] = None
    parent_id: Optional[int] = None


@strawberry.type
class TaskStats:
    task_type: TaskType
    last_run: datetime = datetime.min
    imported: int = 0
    parsed: int = 0
    trimmed: int = 0
    deduped: int = 0
    total_playtime: int = 0
    average_playtime: int = 0
    total_filesize: int = 0
    average_filesize: int = 0
    updated_at: datetime = datetime.now(timezone.utc)


@strawberry.type
class TaskStatSnapshot:
    snapshot_time: datetime = datetime.now(timezone.utc)
    task_type: TaskType
    total_playtime: int = 0
    total_filesize: int = 0
    imported: int = 0
    parsed: int = 0
    trimmed: int = 0
    deduped: int = 0


@strawberry.type
class StatPoint:
    timestamp: datetime
    value: int


@strawberry.type
class TaskStatSummary:
    task_type: TaskType
    imported: StatDelta
    parsed: StatDelta
    trimmed: StatDelta
    deduped: StatDelta
    total_playtime: StatDelta
    total_filesize: StatDelta


@strawberry.type
class StatDelta:
    value: int
    change: int
    percentage: float


@strawberry.type
class TaskStatTrend:
    task_type: TaskType
    imported: List[StatPoint]
    parsed: List[StatPoint]
    trimmed: List[StatPoint]
    deduped: List[StatPoint]
    total_playtime: List[StatPoint]
    total_filesize: List[StatPoint]


T = TypeVar("T")


@strawberry.type
class Paginated(Generic[T]):
    items: list[T]
    total: int


@strawberry.input
class FileInput:
    path: str | None = None
    size: int | None = None
    extension: str | None = None
    codec: str | None = None


@strawberry.type
class FileType:
    id: int
    path: str
    size: int
    extension: str
    codec: str
