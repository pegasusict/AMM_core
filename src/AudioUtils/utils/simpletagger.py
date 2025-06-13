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

"""SimpleTagger class provides methods to retrieve MBID and AcoustID from an audio file's metadata."""

from pathlib import Path
from typing import Optional
from mutagen import File


class SimpleTagger:
    def __init__(self, path: Path) -> None:
        """Initializes the SimpleTagger with a file path."""
        self.audio = File(path)

    def get_mbid(self) -> Optional[str]:
        """Retrieves the MusicBrainz ID (MBID) from the audio file tags."""
        # Fallback to 'mbid' if 'musicbrainz_trackid' is not present
        return (
            self.audio.tags.get("musicbrainz_trackid", [None])[0]  # type: ignore
            or self.audio.tags.get("mbid", [None])[0]  # type: ignore
        )

    def get_acoustid(self) -> Optional[str]:
        """Retrieves the AcoustID from the audio file tags."""
        # Fallback to 'acoustid' if 'acoustid_id' is not present
        return (
            self.audio.tags.get("acoustid_id", [None])[0]  # type: ignore
            or self.audio.tags.get("acoustid", [None])[0]  # type: ignore
        )
