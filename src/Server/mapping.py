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

"""Defines mappings between DB schemas and GraphQL schemas."""

from typing import Any, List, Optional
from sqlmodel import SQLModel

from core.dbmodels import (
    DBAlbum,
    DBAlbumTrack,
    DBFile,
    DBGenre,
    DBKey,
    DBLabel,
    DBPerson,
    DBPicture,
    DBPlaylist,
    DBPlaylistTrack,
    DBQueue,
    DBStat,
    DBTask,
    DBTrack,
    DBTrackLyric,
    DBTrackTag,
    DBUser,
)
from core.enums import Codec
from .schemas import (
    Album,
    AlbumTrack,
    DisplayTask,
    File,
    FileType,
    Genre,
    Key,
    Label,
    Person,
    Picture,
    Playlist,
    PlaylistTrack,
    PlayerTrack,
    Queue,
    Stat,
    Task,
    Track,
    TrackLyric,
    TrackTag,
    User,
)


def _id_list(items: Any) -> list[int]:
    if not items:
        return []
    return [item.id for item in items if getattr(item, "id", None) is not None]


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def map_dbtrack_to_playertrack(track: DBTrack) -> PlayerTrack:
    album_picture = None
    if track.album_tracks:
        first_album = track.album_tracks[0].album
        if first_album and first_album.picture:
            album_picture = str(first_album.picture.picture_path)

    duration_seconds = track.files[0].duration if track.files else None
    lyrics = track.lyric.lyric if track.lyric else None

    return PlayerTrack(
        id=track.id,
        title=getattr(track, "title", None) or track.mbid or f"Track {track.id}",
        subtitle=getattr(track, "subtitle", None),
        artists=["Unknown Artist"],
        album_picture=album_picture,
        duration_seconds=duration_seconds,
        lyrics=lyrics,
    )


def map_dbplaylist_to_playlist(playlist: DBPlaylist) -> Playlist:
    ordered = sorted(playlist.tracks, key=lambda t: t.position)
    return Playlist(
        id=playlist.id,
        name=playlist.name,
        user_id=playlist.user_id,
        playlist_track_ids=_id_list(ordered),
        track_ids=[pltrack.track_id for pltrack in ordered],
    )


def map_dbqueue_track_ids(queue: Optional[DBQueue]) -> List[int]:
    return queue.track_ids if queue else []


def map_dbqueue_to_queue(queue: Optional[DBQueue]) -> Queue:
    if not queue:
        return Queue(id=None, user_id=None, track_ids=[])
    return Queue(id=queue.id, user_id=queue.user_id, track_ids=list(queue.track_ids))


def map_dbtrack_to_track(track: DBTrack) -> Track:
    return Track(
        id=track.id,
        composed=track.composed,
        release_date=track.release_date,
        mbid=track.mbid,
        file_ids=_id_list(track.files),
        album_track_ids=_id_list(track.album_tracks),
        key_id=track.key_id,
        genre_ids=[track.genre_id] if track.genre_id is not None else [],
        performer_ids=[],
        conductor_ids=[],
        composer_ids=[],
        lyricist_ids=[],
        producer_ids=[],
        task_ids=[track.task.id] if track.task and track.task.id is not None else [],
        lyric_id=track.lyric.id if track.lyric else None,
        tracktag_ids=_id_list(track.tracktags),
    )


def map_dbuser_to_user(user: DBUser) -> User:
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        middle_name=user.middle_name,
        last_name=user.last_name,
        date_of_birth=user.date_of_birth,
        role=user.role,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_active=user.is_active,
    )


def map_dbgenre_to_genre(genre: DBGenre) -> Genre:
    return Genre(
        id=genre.id,
        genre=genre.genre,
        description=genre.description,
        track_ids=_id_list(getattr(genre, "tracks", None)),
        album_ids=_id_list(getattr(genre, "albums", None)),
        parent_ids=[],
        child_ids=[],
    )


def map_dbalbum_to_album(album: DBAlbum) -> Album:
    return Album(
        id=album.id,
        mbid=album.mbid,
        title=album.title,
        title_sort=album.title_sort,
        subtitle=album.subtitle,
        release_date=album.release_date,
        release_country=album.release_country,
        disc_count=album.disc_count,
        track_count=album.track_count,
        task_id=album.task_id,
        label_id=album.label_id,
        album_track_ids=_id_list(album.album_tracks),
        genre_ids=[album.genre_id] if album.genre_id is not None else [],
        artist_ids=[],
        conductor_ids=[],
        composer_ids=[],
        lyricist_ids=[],
        producer_ids=[],
        picture_id=None,
    )


def map_dbperson_to_person(person: DBPerson) -> Person:
    return Person(
        id=person.id,
        mbid=person.mbid,
        first_name=person.first_name,
        middle_name=person.middle_name,
        last_name=person.last_name,
        sort_name=person.sort_name,
        full_name=person.full_name,
        nick_name=person.nick_name,
        alias=person.alias,
        date_of_birth=person.date_of_birth,
        date_of_death=person.date_of_death,
        picture_id=None,
        performed_track_ids=[],
        conducted_track_ids=[],
        composed_track_ids=[],
        lyric_track_ids=[],
        produced_track_ids=[],
        performed_album_ids=[],
        conducted_album_ids=[],
        composed_album_ids=[],
        lyric_album_ids=[],
        produced_album_ids=[],
        task_ids=[person.task_id] if person.task_id is not None else [],
        label_ids=_id_list(person.labels),
    )


def map_dblabel_to_label(label: DBLabel) -> Label:
    return Label(
        id=label.id,
        name=label.name,
        mbid=label.mbid,
        description=label.description,
        founded=label.founded,
        defunct=label.defunct,
        owner_id=label.owner_id,
        parent_id=label.parent_id,
        child_ids=_id_list(label.children),
        picture_id=None,
        album_ids=_id_list(label.albums),
    )


def map_dbtask_to_displaytask(task: DBTask) -> Any:
    return DisplayTask(
        task_id=task.task_id,
        task_type=str(_enum_value(task.task_type)),
        status=str(_enum_value(task.status)),
        start_time=task.start_time,
        progress=int(task.progress) if task.progress is not None else 0,
    )


def map_dbtask_to_task(task: DBTask) -> Task:
    return Task(
        id=task.id,
        task_id=task.task_id,
        start_time=task.start_time,
        end_time=task.end_time,
        duration=task.duration,
        processed=task.processed,
        progress=task.progress,
        function=task.function,
        kwargs=task.kwargs,
        result=task.result,
        error=task.error,
        status=str(_enum_value(task.status)),
        task_type=str(_enum_value(task.task_type)),
    )


def map_dbfile_to_file(file: DBFile) -> File:
    return File(
        id=file.id,
        audio_ip=file.audio_ip,
        imported=file.imported,
        processed=file.processed,
        bitrate=file.bitrate,
        sample_rate=file.sample_rate,
        channels=file.channels,
        file_type=file.file_type,
        file_size=file.file_size,
        file_name=file.file_name,
        file_extension=file.file_extension,
        codec=file.codec,
        duration=file.duration,
        track_id=file.track_id,
        task_id=file.task_id,
        file_path=file.file_path,
        stage_type=int(file.stage_type) if file.stage_type is not None else None,
        completed_tasks=list(file.completed_tasks) if file.completed_tasks else [],
    )


def map_dbfile_to_filetype(file: DBFile) -> FileType:
    return FileType(
        id=file.id,
        path=file.file_path or "",
        size=file.file_size or 0,
        extension=file.file_extension or "",
        codec=file.codec.value if file.codec else Codec.UNKNOWN.value,
    )


def map_dbplaylist_track_to_playlist_track(playlist_track: DBPlaylistTrack) -> PlaylistTrack:
    return PlaylistTrack(
        id=playlist_track.id,
        playlist_id=playlist_track.playlist_id,
        track_id=playlist_track.track_id,
        position=playlist_track.position,
    )


def map_dbalbum_track_to_album_track(album_track: DBAlbumTrack) -> AlbumTrack:
    return AlbumTrack(
        id=album_track.id,
        album_id=album_track.album_id,
        track_id=album_track.track_id,
        disc_number=album_track.disc_number,
        track_number=album_track.track_number,
    )


def map_dbtrack_tag_to_track_tag(track_tag: DBTrackTag) -> TrackTag:
    return TrackTag(
        id=track_tag.id,
        track_id=track_tag.track_id,
        tag_type=str(_enum_value(track_tag.tag_type)),
        data=track_tag.data,
    )


def map_dbkey_to_key(key: DBKey) -> Key:
    return Key(id=key.id, key=key.key, track_ids=_id_list(key.tracks))


def map_dbtrack_lyric_to_track_lyric(track_lyric: DBTrackLyric) -> TrackLyric:
    return TrackLyric(
        id=track_lyric.id,
        lyric=track_lyric.lyric,
        track_id=track_lyric.track_id,
    )


def map_dbpicture_to_picture(picture: DBPicture) -> Picture:
    return Picture(
        id=picture.id,
        picture_path=picture.picture_path,
        album_id=picture.album_id,
        person_id=picture.person_id,
        label_id=picture.label_id,
    )


def map_dbstat_to_stat(stat: DBStat) -> Stat:
    return Stat(
        id=stat.id,
        name=stat.name,
        value=stat.value,
        range_start=stat.range_start,
        range_end=stat.range_end,
        unit=stat.unit,
    )


# ------------------ GraphQL Input -> DB Model (Dynamic Reverse Mapping) ------------------


def update_model_from_input(model: SQLModel, input_data: Any) -> SQLModel:
    """
    Generic mapper: Updates DB model fields from GraphQL input.
    Only sets attributes that exist in the model and are not None in the input.
    """
    field_map = {}
    if isinstance(model, DBFile):
        field_map = {
            "path": "file_path",
            "extension": "file_extension",
            "size": "file_size",
        }
    elif isinstance(model, DBGenre):
        field_map = {
            "name": "genre",
        }

    for field_name, value in input_data.__dict__.items():
        target_name = field_map.get(field_name, field_name)
        if value is not None and hasattr(model, target_name):
            if target_name == "codec" and isinstance(value, str):
                try:
                    value = Codec[value]
                except KeyError:
                    try:
                        value = Codec(value)
                    except Exception:
                        pass
            setattr(model, target_name, value)
    return model
