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

from ..models import Stage, UserRole, Codec, DateType


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
class Stat:
    """Stat type for GraphQL schema."""

    id: int | None = None
    name: str | None = None
    value: int | float | None = None
    range_start: int | float | None = None
    range_end: int | float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@strawberry.type()
class File:
    """File type for GraphQL schema."""

    id: int | None = None
    imported: datetime | None = None
    processed: datetime | None = None
    file_path: Path | None = None
    file_name: str | None = None
    file_type: str | None = None
    size: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    codec: Codec | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    duration: int | None = None
    stage: Stage | None = None


@strawberry.type()
class Track:
    """Track type for GraphQL schema."""

    id: int | None = None
    title: str | None = None
    title_sort: str | None = None
    subtitle: str | None = None
    artists: List[int] | None = None  # artist name
    year: int | None = None
    albums: List[int] | None = None  # album id
    files: List[int] | None = None  # File id
    key: str | None = None
    releasedate: date | None = None
    genres: List[int] | None = None  # genre id
    mbid: str | None = None
    label: str | None = None
    lyrics: str | None = None


@strawberry.type()
class Album:
    """Album type for GraphQL schema."""

    id: int | None = None
    title: str | None = None
    subtitle: str | None = None
    artists: List[int] | None = None  # artist id
    tracks: List[int] | None = None  # track id
    key: str | None = None
    releasedate: date | None = None
    genres: List[int] | None = None  # genre id
    mbid: str | None = None
    label: str | None = None
    picture: Path | None = None
    disc_count: int | None = None
    track_count: int | None = None
    release_country: str | None = None


@strawberry.type()
class Genre:
    """Genre type for GraphQL schema."""

    id: int | None = None
    name: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    albums: List[int] | None = None  # album id
    tracks: List[int] | None = None  # track id
    parents: List[int] | None = None  # Genre id
    children: List[int] | None = None  # Genre id


@strawberry.type()
class Person:
    """Person type for GraphQL schema."""

    id: int | None = None
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    alias: str | None = None
    nick_name: str | None = None
    sort_name: str | None = None
    date_of_birth: date | None = None
    date_of_death: date | None = None
    picture: Path | None = None
    mbid: str | None = None
    performed_tracks: List[int] | None = None  # Track id
    performed_albums: List[int] | None = None  # Album id


@strawberry.type()
class Date:
    """Date type for GraphQL schema."""

    id: int | None = None
    date: date | None = None
    type: DateType | None = None
    person: int | None = None  # Person id
    track: int | None = None  # Track id
    album: int | None = None  # Album id


@strawberry.type()
class Label:
    """Label type for GraphQL schema."""

    id: int | None = None
    name: str | None = None
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    albums: List[int] | None = None  # Album id


@strawberry.type()
class Key:
    """Key type for GraphQL schema."""

    id: int | None = None
    name: str | None = None


@strawberry.type()
class FilePath:
    """FilePath type for GraphQL schema."""

    id: int | None = None
    path: Path | None = None
    definitive: bool | None = None  # TODO: do we need this field?
    file: int | None = None  # File id


@strawberry.type()
class MBid:
    """MBid type for GraphQL schema."""

    id: int | None = None
    mbid: str | None = None
    track: int | None = None  # Track id
    album: int | None = None  # Album id
    person: int | None = None  # Person id
    label: int | None = None  # Label id
