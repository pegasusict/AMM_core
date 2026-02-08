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
from datetime import datetime, date
from pathlib import Path
from typing import List

import strawberry
from pydantic import EmailStr

from Enums import Stage, UserRole, Codec


@strawberry.type()
class User:
    """User type for GraphQL schema."""

    id: int | None = None
    username: str | None = None
    password_hash: str | None = None
    email: EmailStr | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    role: UserRole | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool | None = None


@strawberry.type()
class Task:
    """Task type for GraphQL schema."""

    id: int | None = None
    task_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration: int | None = None
    batch_files: list[int] | None = None  # File id
    batch_tracks: list[int] | None = None  # Track id
    batch_albums: list[int] | None = None  # Album id
    batch_persons: list[int] | None = None  # Person id
    batch_labels: list[int] | None = None  # Label id
    batch_convert: list[int] | None = None  # File id
    processed: int | None = None
    progress: int | None = None
    function: str | None = None
    kwargs: str | None = None
    result: str | None = None
    error: str | None = None
    status: str | None = None
    task_type: str | None = None


@strawberry.type()
class Stat:
    """Stat type for GraphQL schema."""

    id: int | None = None
    name: str | None = None
    value: int | float | None = None
    range_start: int | float | None = None
    range_end: int | float | None = None
    unit: str | None = None


@strawberry.type()
class File:
    """File type for GraphQL schema."""

    id: int | None = None
    imported: datetime | None = None
    processed: datetime | None = None
    file_path: Path | None = None
    file_name: str | None = None
    file_type: str | None = None
    file_extension: str | None = None
    size: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    codec: Codec | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    duration: int | None = None
    stage: Stage | None = None
    fingerprint: str | None = None
    track_id: int | None = None
    task_id: int | None = None
    batch_id: int | None = None


@strawberry.type()
class Track:
    """Track type for GraphQL schema."""

    id: int | None = None
    title: str | None = None
    title_sort: str | None = None
    subtitle: str | None = None
    artists: List[int] | None = None  # person id
    albums: List[int] | None = None  # album id
    key: str | None = None
    genres: List[int] | None = None  # genre id
    mbid: str | None = None
    conductors: List[int] | None = None  # person id
    composers: List[int] | None = None  # person id
    lyricists: List[int] | None = None  # person id
    producers: List[int] | None = None  # person id
    releasedate: date | None = None
    lyrics: str | None = None
    files: List[int] | None = None  # File id
    task_id: int | None = None


@strawberry.type()
class Album:
    """Album type for GraphQL schema."""

    id: int | None = None
    mbid: str | None = None
    title: str | None = None
    title_sort: str | None = None
    subtitle: str | None = None
    releasedate: date | None = None
    release_country: str | None = None
    label: str | None = None
    tracks: list[int] | None = None  # track id
    genres: List[int] | None = None  # genre id
    artists: List[int] | None = None  # person id
    conductors: List[int] | None = None  # person id
    composers: List[int] | None = None  # person id
    lyricists: List[int] | None = None  # person id
    producers: List[int] | None = None  # person id
    picture: Path | None = None
    disc_count: int | None = None
    track_count: int | None = None
    task_id: int | None = None


@strawberry.type()
class Genre:
    """Genre type for GraphQL schema."""

    id: int | None = None
    name: str | None = None
    description: str | None = None
    albums: List[int] | None = None  # album id
    tracks: List[int] | None = None  # track id
    parents: List[int] | None = None  # Genre id
    children: List[int] | None = None  # Genre id


@strawberry.type()
class Person:
    """Person type for GraphQL schema."""

    id: int | None = None
    mbid: str | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    alias: str | None = None
    nick_name: str | None = None
    sort_name: str | None = None
    date_of_birth: date | None = None
    date_of_death: date | None = None
    picture: Path | None = None
    performed_tracks: List[int] | None = None  # Track id
    conducted_tracks: List[int] | None = None  # Track id
    composed_tracks: List[int] | None = None  # Track id
    lyric_tracks: List[int] | None = None  # Track id
    produced_tracks: List[int] | None = None  # Track id
    performed_albums: List[int] | None = None  # Album id
    conducted_albums: List[int] | None = None  # Album id
    composed_albums: List[int] | None = None  # Album id
    lyric_albums: List[int] | None = None  # Album id
    produced_albums: List[int] | None = None  # Album id
    task_id: int | None = None
    labels: List[int] | None = None  # Label id


@strawberry.type()
class Label:
    """Label type for GraphQL schema."""

    id: int | None = None
    name: str | None = None
    mbid: str | None = None
    description: str | None = None
    founded: datetime | None = None
    defunct: datetime | None = None
    albums: List[int] | None = None  # Album id
    picture: Path | None = None
    parent: int | None = None  # Label id
    children: List[int] | None = None  # Label id
    owner: int | None = None  # Person id


@strawberry.type()
class Key:
    """Key type for GraphQL schema."""

    id: int | None = None
    name: str | None = None
    tracks: list[int] | None = None  # Track id
