# -*- coding: utf-8 -*-
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

"""Pydantic Models for the application."""

from typing import List, Optional, Any
import datetime as dt

from pydantic import BaseModel
from sqlmodel import select
from sqlalchemy.orm import selectinload

from .exceptions import InvalidValueError
from Singletons import DBInstance
from dbmodels import DBFile, DBTrack, DBPerson, DBAlbum, DBAlbumTrack


class ArtistModel(BaseModel):
    name: str
    mbid: Optional[str] = None


class MetadataModel(BaseModel):
    artists: List[ArtistModel] = []
    title: Optional[str] = None
    mbid: Optional[str] = None


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
    releasedate: dt.date = dt.date.min
    producers: List[str] = [""]
    task: str = ""
    files: List["DBFile"] = []  # List of File ids

    def __init__(self, track_id: int | None = None) -> None:
        if track_id is not None:
            self.id = track_id

    @classmethod
    async def from_id(cls, track_id: int) -> "Track":
        """Async loader for Track from the database."""
        async for session in DBInstance.get_session():
            result = await session.exec(
                select(DBTrack)
                .where(DBTrack.id == track_id)
                .options(
                    selectinload(DBTrack.albums),  # type: ignore
                    selectinload(DBTrack.files),  # type: ignore
                    selectinload(DBTrack.artists),  # type: ignore
                    selectinload(DBTrack.album_tracks),  # type: ignore
                    # Add more as needed
                )
            )
            trackdata = result.first()
            await session.close()
            if not trackdata:
                raise InvalidValueError(
                    f"Track with id {track_id} not found in the database."
                )

            obj = cls(track_id=track_id)
            for key, value in trackdata.__dict__.items():
                setattr(obj, key, value or None)
            return obj

        raise InvalidValueError(f"Track with id {track_id} not found in the database.")


    @property
    def tags(self) -> dict[str, str | int | dt.date]:
        return {
            "title": self.title,
            "subtitle": self.subtitle or "",
            "titlesort": self.title_sort,
            "artists": ",".join(
                map(
                    str,
                    [DBPerson(id=artist_id).full_name for artist_id in self.artists],
                )
            ),
            "albums": ",".join(
                map(str, [DBAlbum(id=album_id).title for album_id in self.albums])
            ),
            "key": self.key,
            "genres": ",".join(map(str, self.genres)),
            "mbid": self.mbid,
            "conductors": ",".join(map(str, self.conductors)),
            "composers": ",".join(map(str, self.composers)),
            "lyricists": ",".join(map(str, self.lyricists)),
            "releasedate": self.releasedate,
            "producers": ",".join(map(str, self.producers)),
        }

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
            "album_title_sort": safe(
                getattr(album, "title_sort", None), "[Unknown Album]"
            ),
            "year": str(
                safe(getattr(album, "release_date", None), "0000").year
                if album
                else "0000"
            ),
            "disc_number": str(safe(getattr(album_track, "disc_number", None), 1)),
            "disc_count": str(safe(getattr(album, "disc_count", None), 1)),
            "track_count": str(safe(getattr(album, "track_count", None), 1)),
            "track_number": str(safe(getattr(album_track, "track_number", None), 1)),
            "bitrate": safe(getattr(file, "bitrate", None), 0),
            "duration": safe(getattr(file, "length", None), 0),
        }

    def _get_album(self) -> DBAlbum | None:
        return DBAlbum(id=self.albums[0]) if self.albums else None

    def _get_album_track(self, album_id: int) -> DBAlbumTrack | None:
        return DBAlbumTrack(album_id=album_id, track_id=self.id) if self.id else None

    def _get_artist(self) -> DBPerson | None:
        return DBPerson(id=self.artists[0]) if self.artists else None
