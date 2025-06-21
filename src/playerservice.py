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

"""This module contains the music player service."""

from pathlib import Path
from typing import Optional, List

import vlc


class TrackItem:
    """Represents a single track item with an associated file ID and file path.
    This class is used to store information about a track in the player queue."""

    def __init__(self, file_id: int, path: Path):
        self.id = file_id
        self.path = path


class PlayerService:
    """Provides music playback functionality and manages a queue of tracks.
    This service allows tracks to be queued, played, paused, and stopped,
    and provides status information about playback."""

    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()  # type: ignore
        self.queue: List[TrackItem] = []
        self.current_track: Optional[TrackItem] = None

    def add_to_queue(self, track_path: Path, file_id: int) -> None:
        """Adds a track to the queue."""
        self.queue.append(TrackItem(file_id, track_path))

    def play_next(self) -> None:
        """Skips to the next track in the queue.
        If the queue is empty, it stops."""
        if not self.queue:
            self.current_track = None
            return

        self.current_track = self.queue.pop(0)
        media = self.instance.media_new(str(self.current_track.path))  # type: ignore
        self.player.set_media(media)
        self.player.play()

    def pause(self) -> None:
        """Pauses playback."""
        self.player.pause()

    def stop(self) -> None:
        """Stops playback."""
        self.player.stop()

    def get_status(self) -> dict:
        """Returns the current status, concisting of:
        current track, playback state, contents of the queue."""
        return {
            "current": self.current_track,
            "state": self.player.get_state().name,
            "queue": self.queue,
        }
