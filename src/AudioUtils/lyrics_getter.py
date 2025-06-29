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

"""This module retrieves lyrics from internet"""

from lyricsgenius.genius import Genius


class LyricsGetter:
    """This class retrieves lyrics from the internet."""

    def __init__(self):
        self.genius = Genius()  # type: ignore
        self.genius.remove_section_headers = True  # type: ignore

    def get_lyrics(self, artist: str, title: str) -> str:
        """Retrieve lyrics for said song."""
        return self.genius.search_song(title, artist)  # type: ignore
