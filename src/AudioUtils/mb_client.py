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

"""This Module communicates with the server of MusicBrainz.
It uses the musicbrainzngs library to communicate with the MusicBrainz API.
It is used to retrieve information about artists, albums, and tracks.
It is also used to retrieve the cover art for albums and artists.
"""

import musicbrainzngs
from musicbrainzngs import NetworkError, WebServiceError, ResponseError

from Exceptions import InvalidValueError
from Singletons.config import Config
from Singletons.logger import Logger
from Enums import MBQueryType


class MusicBrainzClient:
    """This Class communicates with the server of MusicBrainz."""

    def __init__(self, config: Config) -> None:
        """Initializes the ArtGetter class."""
        self.logger = Logger(config)
        self.config = config
        self.musicbrainz = musicbrainzngs
        self.musicbrainz.set_useragent("Audiophiles' Music Manager", "0.1", "pegasus.ict@gmail.com")
        self.musicbrainz.set_rate_limit(True)

    def get_art(self, mbid: str) -> str | None:
        """
        Retrieves album art from online archives.

        Args:
                mbid: The MusicBrainz ID of the album/artist.

        Returns:
                The URL of the album/artist art.
        """
        try:
            result = self.musicbrainz.get_image_list(mbid)
            if result["images"]:
                return result["images"][0]["thumbnails"]["large"]
            else:
                return None
        except (NetworkError, WebServiceError) as e:
            self.logger.error(f"Error retrieving art: {e}")
            return None

    def _get_by_id(self, query_type: MBQueryType, mbid: str) -> dict | None:
        """Gets item by id

        Args:
                query_type (QueryType):     artist,album,release,track,recording
                mbid (str):                 MusicBrainz ID

        Returns:
                dict|None: A dictionary with the item information or None if not found.
        """
        try:
            result = ""
            match query_type:
                case MBQueryType.ARTIST:
                    result = self.musicbrainz.get_artist_by_id(mbid)
                case MBQueryType.RECORDING:
                    result = self.musicbrainz.get_recording_by_id(mbid)
                case MBQueryType.TRACK:
                    result = self.musicbrainz.get_recording_by_id(mbid)
                case MBQueryType.RELEASE:
                    result = self.musicbrainz.get_release_by_id(mbid)
                case MBQueryType.ALBUM:
                    result = self.musicbrainz.get_release_by_id(mbid)
                case MBQueryType.RELEASE_GROUP:
                    result = self.musicbrainz.get_release_group_by_id(mbid)
                case _:
                    raise InvalidValueError(f"Not a correct QueryType: {query_type}")
            return result
        except (ResponseError, NetworkError, WebServiceError) as e:
            self.logger.error(f"Error retrieving {query_type} info by id: {e}")
            return None

    def get_artist_by_id(self, mbid: str) -> dict | None:
        """
        Retrieves artist information by MusicBrainz ID.

        Args:
                mbid: The MusicBrainz ID of the artist.

        Returns:
                The artist information.
        """
        return self._get_by_id(MBQueryType.ARTIST, mbid)

    def get_release_by_id(self, mbid: str) -> dict | None:
        """
        Retrieves release information by MusicBrainz ID.

        Args:
                mbid: The MusicBrainz ID of the release.

        Returns:
                The release information.
        """
        return self._get_by_id(MBQueryType.RELEASE, mbid)

    def get_release_group_by_id(self, mbid: str) -> dict | None:
        """
        Retrieves release_group information by MusicBrainz ID.

        Args:
                mbid: The MusicBrainz ID of the release_group.

        Returns:
                The release_group information.
        """
        return self._get_by_id(MBQueryType.RELEASE_GROUP, mbid)

    def get_recording_by_id(self, mbid: str) -> dict | None:
        """
        Retrieves recording information by MusicBrainz ID.

        Args:
                mbid: The MusicBrainz ID of the recording.

        Returns:
                The recording information.
        """
        return self._get_by_id(MBQueryType.RECORDING, mbid)

    def get_track_by_id(self, mbid: str) -> dict | None:
        """
        Retrieves track information by MusicBrainz ID.

        Args:
                mbid: The MusicBrainz ID of the track.

        Returns:
                The track information.
        """
        return self._get_by_id(MBQueryType.TRACK, mbid)

    def get_album_by_id(self, mbid: str) -> dict | None:
        """
        Retrieves album information by MusicBrainz ID.

        Args:
                mbid: The MusicBrainz ID of the album.

        Returns:
                The album information.
        """
        return self._get_by_id(MBQueryType.ALBUM, mbid)

    def _get_by_name(self, query_type: MBQueryType, name: str) -> dict | None:
        """
        Retrieves information by name.

        Args:
                query_type: artist/album/track/recording/release/release_group
                name: The name of the item.

        Returns:
                The requested information.
        """
        try:
            result = ""
            match query_type:
                case MBQueryType.ARTIST:
                    result = self.musicbrainz.search_artists(name=name)
                case MBQueryType.ALBUM:
                    result = self.musicbrainz.search_releases(name=name)
                case MBQueryType.TRACK:
                    result = self.musicbrainz.search_recordings(name=name)
                case MBQueryType.RECORDING:
                    result = self.musicbrainz.search_recordings(name=name)
                case MBQueryType.RELEASE:
                    result = self.musicbrainz.search_releases(name=name)
                case MBQueryType.RELEASE_GROUP:
                    result = self.musicbrainz.search_release_groups(name=name)
                case _:
                    raise InvalidValueError(f"Not a correct QueryType: {query_type}")
            return result
        except (ResponseError, NetworkError, WebServiceError) as e:
            self.logger.error(f"Error retrieving {query_type} info: {e}")
            return None

    def get_artist_by_name(self, name: str) -> dict | None:
        """
        Retrieves artist information by name.

        Args:
                name: The name of the artist.

        Returns:
                The artist information.
        """
        return self._get_by_name(MBQueryType.ARTIST, name)

    def get_album_by_name(self, name: str) -> dict | None:
        """
        Retrieves album information by name.

        Args:
                name: The name of the album.

        Returns:
                The album information.
        """
        return self._get_by_name(MBQueryType.ALBUM, name)

    def get_track_by_name(self, name: str) -> dict | None:
        """
        Retrieves track information by name.

        Args:
                name: The name of the track.

        Returns:
                The track information.
        """
        return self._get_by_name(MBQueryType.TRACK, name)

    def get_release_group_by_name(self, name: str) -> dict | None:
        """
        Retrieves release group information by name.

        Args:
                name: The name of the release group.

        Returns:
                The release group information.
        """
        return self._get_by_name(MBQueryType.RELEASE_GROUP, name)

    def get_recording_by_name(self, name: str) -> dict | None:
        """
        Retrieves recording information by name.

        Args:
                name: The name of the recording.

        Returns:
                The recording information.
        """
        return self._get_by_name(MBQueryType.RECORDING, name)

    def get_release_by_name(self, name: str) -> dict | None:
        """
        Retrieves release information by name.

        Args:
                name: The name of the release.

        Returns:
                The release information.
        """
        return self._get_by_name(MBQueryType.RELEASE, name)

    def get_track_by_audio_fingerprint(self, fingerprint: str) -> dict | None:
        """
        Retrieves track information by audio fingerprint.

        Args:
                fingerprint: The audio fingerprint of the track.

        Returns:
                The track information.
        """
        try:
            result = self.musicbrainz.search_recordings(fingerprint=fingerprint)
            return result
        except (ResponseError, NetworkError, WebServiceError) as e:
            self.logger.error(f"Error retrieving track info: {e}")
            return None
