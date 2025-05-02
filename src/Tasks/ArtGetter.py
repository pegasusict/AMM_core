# -*- coding: utf-8 -*-
#  Copyleft 2021-2024 Mattijs Snepvangers.
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

    def __init__(self):
        """
        Initialize the ArtGetter class.
        """
        pass

    def get_art(self, artist: str, album: str|None=None) -> None:
        """
        Get the art for a given artist and album.

        :param artist: The name of the artist.
        :param album: The name of the album.
        :return: The URL of the art.
        """
        # Placeholder implementation
        f"https://example.com/art/{artist}/{album}.jpg"