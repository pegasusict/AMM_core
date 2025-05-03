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
"""Retrieves art from online archives."""

from enum import Enum
import musicbrainzngs

class ArtType(Enum):
    """
    Enum for different types of art.
    """
    ALBUM = "album"
    ARTIST = "artist"

class ArtGetter:
    """
    This class retrieves art from online archives.
    """

    def __init__(self, config):
        """
        Initializes the ArtGetter class.

        Args:
            config: The configuration object.
        """
        self.config = config
        self.musicbrainz = musicbrainzngs
        self.musicbrainz.set_useragent("Audiophiles Music Manager", "0.1")
        self.musicbrainz.set_rate_limit(True)


    def get_art(self, mbid:str, art_type:ArtType)->str:
        """
        Retrieves art from online archives.

        Args:
            mbid: The MusicBrainz ID of the album or artist.
            art_type: The type of art to retrieve (album or artist).

        Returns:
            The URL of the art.
        """
        if art_type == ArtType.ALBUM:
            return self.get_album_art(mbid)
        elif art_type == ArtType.ARTIST:
            return self.get_artist_art(mbid)
        else:
            raise ValueError("Invalid art type. Use 'album' or 'artist'.")


    def get_album_art(self, mbid):
        """
        Retrieves album art from online archives.

        Args:
            mbid: The MusicBrainz ID of the album.

        Returns:
            The URL of the album art.
        """
        try:
            result = self.musicbrainz.get_release_group_by_id(mbid, includes=["release-group-rels"])
            if "release-group" in result and "images" in result["release-group"]:
                images = result["release-group"]["images"]
                if images:
                    return images[0]["image"]
        except musicbrainzngs.WebServiceError as e:
            print(f"Error retrieving album art: {e}")
        return None

    def get_artist_art(self, mbid):
        """
        Retrieves artist art from online archives.
        Args:
            mbid: The MusicBrainz ID of the artist.
        Returns:
            The URL of the artist art.
        """
        try:
            result = self.musicbrainz.get_artist_by_id(mbid, includes=["artist-rels"])
            if "artist" in result and "images" in result["artist"]:
                images = result["artist"]["images"]
                if images:
                    return images[0]["image"]
        except musicbrainzngs.WebServiceError as e:
            print(f"Error retrieving artist art: {e}")
        return None
