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

"""Contains the GraphQL schemas."""

from __future__ import annotations
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

import strawberry
from pydantic import EmailStr

from ..enums import Stage, UserRole, Codec


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
    founded: Optional[datetime] = None
    defunct: Optional[datetime] = None
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
    mbid: str


@strawberry.type
class PlayerStatus:
    current_track: Optional[PlayerTrack]
    is_playing: bool


@strawberry.type
class Playlist:
    id: int
    name: str
    track_ids: List[int]


# ----------------- Mutation Input Types -----------------


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
