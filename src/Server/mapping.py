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

"""Defines mappings between DB schemas and GraphQL schemas."""

from typing import List, Optional, Any
from sqlmodel import SQLModel

from ..dbmodels import (
    DBLabel,
    DBTask,
    DBTrack,
    DBPlaylist,
    DBQueue,
    DBUser,
    DBGenre,
    DBAlbum,
    DBPerson,
)
from .schemas import (
    DisplayTask,
    PlayerTrack,
    Playlist,
    User,
    Track,
    Album,
    Genre,
    Person,
    Label,
)


def map_dbtrack_to_playertrack(track: DBTrack) -> PlayerTrack:
    album_picture = track.album_tracks[0].album.picture.picture_path if track.album_tracks[0].album and track.album_tracks[0].album.picture else None

    return PlayerTrack(
        id=track.id,
        title=track.title,
        subtitle=track.subtitle,
        artists=[artist.full_name for artist in track.performers] if track.performers else ["Unknown Artist"],
        album_picture=album_picture,  # type: ignore
        duration_seconds=track.files[0].duration,
        lyrics=track.lyrics,  # type: ignore
    )


def map_dbplaylist_to_playlist(playlist: DBPlaylist) -> Playlist:
    return Playlist(
        id=playlist.id,  # type: ignore
        name=playlist.name,
        track_ids=[pltrack.track_id for pltrack in playlist.tracks],
    )  # type: ignore


def map_dbqueue_track_ids(queue: Optional[DBQueue]) -> List[int]:
    return queue.track_ids if queue else []


def map_dbtrack_to_track(track: DBTrack) -> Track:
    return Track(
        id=track.id,
        title=track.title,
        title_sort=track.title_sort,
        mbid=track.mbid,
        releasedate=track.release_date,
        files=[f.id for f in track.files] if track.files else [],
    )


def map_dbuser_to_user(user: DBUser) -> User:
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        middle_name=user.middle_name,
        last_name=user.last_name,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_active=user.is_active,
    )


def map_dbgenre_to_genre(genre: DBGenre) -> Genre:
    return Genre(
        id=genre.id,
        name=genre.genre,
        description=genre.description,
        albums=[a.id for a in genre.albums] if genre.albums else [],
        tracks=[t.id for t in genre.tracks] if genre.tracks else [],
    )


def map_dbalbum_to_album(album: DBAlbum) -> Album:
    return Album(
        id=album.id,
        title=album.title,
        mbid=album.mbid,
        tracks=[t.track.id for t in album.album_tracks] if album.album_tracks else [],
    )


def map_dbperson_to_person(person: DBPerson) -> Person:
    return Person(
        id=person.id,
        full_name=person.full_name,
        date_of_birth=person.date_of_birth,
        date_of_death=person.date_of_death,
        alias=person.alias,
        nick_name=person.nick_name,
        sort_name=person.sort_name,
    )


def map_dblabel_to_label(label: DBLabel) -> Label:
    return Label(
        id=label.id,
        name=label.name,
        mbid=label.mbid,
        description=label.description,
        founded=label.founded,
        defunct=label.defunct,
        albums=[a.id for a in label.albums] if label.albums else [],
        picture=label.picture.picture_path if label.picture else None,
        parent=label.parent.id if label.parent else None,
        children=[c.id for c in label.children] if label.children else [],
    )


def map_dbtask_to_displaytask(task: DBTask) -> Any:
    return DisplayTask(
        task_id=task.task_id,
        task_type=task.task_type,
        status=task.status,
        start_time=task.start_time,
        progress=int(task.progress) if task.progress is not None else 0,
    )


# ------------------ GraphQL Input → DB Model (Dynamic Reverse Mapping) ------------------


def update_model_from_input(model: SQLModel, input_data: Any) -> SQLModel:
    """
    Generic mapper: Updates DB model fields from GraphQL input.
    Only sets attributes that exist in the model and are not None in the input.
    """
    for field_name, value in input_data.__dict__.items():
        if value is not None and hasattr(model, field_name):
            setattr(model, field_name, value)
    return model
