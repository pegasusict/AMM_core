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
from typing import Generic, List, Optional, TypeVar

import strawberry

from Enums import TaskType, UserRole, Codec


# ----------------- User & Task -----------------


@strawberry.type()
class User:
    id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
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
    processed: Optional[int] = None
    progress: Optional[float] = None
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
    audio_ip: Optional[str] = None
    imported: Optional[datetime] = None
    processed: Optional[datetime] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    file_extension: Optional[str] = None
    codec: Optional[Codec] = None
    duration: Optional[int] = None
    track_id: Optional[int] = None
    task_id: Optional[int] = None
    file_path: Optional[str] = None
    stage_type: Optional[int] = None
    completed_tasks: Optional[List[str]] = None


@strawberry.type()
class Track:
    id: Optional[int] = None
    composed: Optional[date] = None
    release_date: Optional[date] = None
    mbid: Optional[str] = None
    file_ids: Optional[List[int]] = None
    album_track_ids: Optional[List[int]] = None
    key_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    performer_ids: Optional[List[int]] = None
    conductor_ids: Optional[List[int]] = None
    composer_ids: Optional[List[int]] = None
    lyricist_ids: Optional[List[int]] = None
    producer_ids: Optional[List[int]] = None
    task_ids: Optional[List[int]] = None
    lyric_id: Optional[int] = None
    tracktag_ids: Optional[List[int]] = None


@strawberry.type()
class Album:
    id: Optional[int] = None
    mbid: Optional[str] = None
    title: Optional[str] = None
    title_sort: Optional[str] = None
    subtitle: Optional[str] = None
    release_date: Optional[date] = None
    release_country: Optional[str] = None
    disc_count: Optional[int] = None
    track_count: Optional[int] = None
    task_id: Optional[int] = None
    label_id: Optional[int] = None
    album_track_ids: Optional[List[int]] = None
    genre_ids: Optional[List[int]] = None
    artist_ids: Optional[List[int]] = None
    conductor_ids: Optional[List[int]] = None
    composer_ids: Optional[List[int]] = None
    lyricist_ids: Optional[List[int]] = None
    producer_ids: Optional[List[int]] = None
    picture_id: Optional[int] = None


@strawberry.type()
class Genre:
    id: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    track_ids: Optional[List[int]] = None
    album_ids: Optional[List[int]] = None
    parent_ids: Optional[List[int]] = None
    child_ids: Optional[List[int]] = None


@strawberry.type()
class Person:
    id: Optional[int] = None
    mbid: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    sort_name: Optional[str] = None
    full_name: Optional[str] = None
    nick_name: Optional[str] = None
    alias: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    picture_id: Optional[int] = None
    performed_track_ids: Optional[List[int]] = None
    conducted_track_ids: Optional[List[int]] = None
    composed_track_ids: Optional[List[int]] = None
    lyric_track_ids: Optional[List[int]] = None
    produced_track_ids: Optional[List[int]] = None
    performed_album_ids: Optional[List[int]] = None
    conducted_album_ids: Optional[List[int]] = None
    composed_album_ids: Optional[List[int]] = None
    lyric_album_ids: Optional[List[int]] = None
    produced_album_ids: Optional[List[int]] = None
    task_ids: Optional[List[int]] = None
    label_ids: Optional[List[int]] = None


@strawberry.type()
class Label:
    id: Optional[int] = None
    name: Optional[str] = None
    mbid: Optional[str] = None
    founded: Optional[date] = None
    defunct: Optional[date] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None
    parent_id: Optional[int] = None
    child_ids: Optional[List[int]] = None
    picture_id: Optional[int] = None
    album_ids: Optional[List[int]] = None


@strawberry.type()
class Key:
    id: Optional[int] = None
    key: Optional[str] = None
    track_ids: Optional[List[int]] = None


@strawberry.type
class TrackTag:
    id: Optional[int] = None
    track_id: Optional[int] = None
    tag_type: Optional[str] = None
    data: Optional[str] = None


@strawberry.type
class AlbumTrack:
    id: Optional[int] = None
    album_id: Optional[int] = None
    track_id: Optional[int] = None
    disc_number: Optional[int] = None
    track_number: Optional[int] = None


@strawberry.type
class TrackLyric:
    id: Optional[int] = None
    lyric: Optional[str] = None
    track_id: Optional[int] = None


@strawberry.type
class Picture:
    id: Optional[int] = None
    picture_path: Optional[str] = None
    album_id: Optional[int] = None
    person_id: Optional[int] = None
    label_id: Optional[int] = None


# ----------------- PlayerService + Playlist/Queue -----------------


@strawberry.type
class PlayerTrack:
    id: int
    title: str
    subtitle: Optional[str]
    artists: List[str]
    album_picture: Optional[str]
    duration_seconds: Optional[int]
    lyrics: Optional[str] = None


@strawberry.type
class PlayerStatus:
    current_track: Optional[PlayerTrack]
    is_playing: bool


@strawberry.type
class PlaylistTrack:
    id: Optional[int] = None
    playlist_id: Optional[int] = None
    track_id: Optional[int] = None
    position: Optional[int] = None


@strawberry.type
class Playlist:
    id: Optional[int] = None
    name: Optional[str] = None
    user_id: Optional[int] = None
    playlist_track_ids: Optional[List[int]] = None
    track_ids: Optional[List[int]] = None


@strawberry.type
class Queue:
    id: Optional[int] = None
    user_id: Optional[int] = None
    track_ids: Optional[List[int]] = None


@strawberry.type
class AuthPayload:
    access_token: str
    refresh_token: str
    user: User


# ----------------- Mutation Input Types -----------------


@strawberry.input
class UserCreateInput:
    username: str
    email: str
    password_hash: str
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


@strawberry.input
class UserUpdateInput:
    username: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


@strawberry.input
class TrackInput:
    composed: Optional[date] = None
    release_date: Optional[date] = None
    mbid: Optional[str] = None


@strawberry.input
class AlbumInput:
    mbid: Optional[str] = None
    title: Optional[str] = None
    title_sort: Optional[str] = None
    subtitle: Optional[str] = None
    release_date: Optional[date] = None
    release_country: Optional[str] = None
    disc_count: Optional[int] = None
    track_count: Optional[int] = None
    task_id: Optional[int] = None


@strawberry.input
class PersonInput:
    mbid: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    sort_name: Optional[str] = None
    full_name: Optional[str] = None
    nick_name: Optional[str] = None
    alias: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None


@strawberry.input
class GenreInput:
    genre: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


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
    id: Optional[int] = None
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
    id: Optional[int] = None
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
    imported: "StatDelta"
    parsed: "StatDelta"
    trimmed: "StatDelta"
    deduped: "StatDelta"
    total_playtime: "StatDelta"
    total_filesize: "StatDelta"


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
    audio_ip: str | None = None
    imported: datetime | None = None
    processed: datetime | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    file_type: str | None = None
    file_size: int | None = None
    file_name: str | None = None
    file_extension: str | None = None
    codec: str | None = None
    duration: int | None = None
    track_id: int | None = None
    task_id: int | None = None
    file_path: str | None = None
    stage_type: int | None = None
    completed_tasks: list[str] | None = None
    # Legacy aliases
    path: str | None = None
    size: int | None = None
    extension: str | None = None


@strawberry.type
class FileType:
    id: int
    path: str
    size: int
    extension: str
    codec: str
