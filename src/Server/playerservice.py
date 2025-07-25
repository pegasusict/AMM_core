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

import subprocess
from typing import Dict, List, Optional

from ..dbmodels import DBQueue, DBTrack
from ..Singletons import EnvConfig
from ..Singletons.database import DBInstance


class PlayerService:
    """Handles playback (via VLC) per user - outputs to unique Icecast mount."""

    _instances: Dict[int, "PlayerService"] = {}

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.queue: List[int] = []  # track IDs
        self.current_process: Optional[subprocess.Popen] = None
        self.is_playing = False

    @classmethod
    async def get_instance(cls, user_id: int) -> "PlayerService":
        """Get or create PlayerService instance for user."""
        if user_id not in cls._instances:
            service = cls(user_id)
            await service.load_queue_from_db()
            cls._instances[user_id] = service
        return cls._instances[user_id]

    async def load_queue_from_db(self):
        """Load user's persistent queue from DB."""
        async for session in DBInstance.get_session():
            result = await session.get_one(DBQueue, DBQueue.user_id == self.user_id)
            if db_queue := result:
                self.queue = db_queue.track_ids

    async def save_queue_to_db(self):
        """Persist queue to DB."""
        async for session in DBInstance.get_session():
            result = await session.get_one(DBQueue, DBQueue.user_id == self.user_id)
            if db_queue := result:
                db_queue.track_ids = self.queue
            else:
                db_queue = DBQueue(user_id=self.user_id, track_ids=self.queue)
                session.add(db_queue)

            await session.commit()

    async def queue_track(self, track_id: int):
        """Add track to the end of queue."""
        self.queue.append(track_id)
        await self.save_queue_to_db()

    async def play_next(self):
        """Play the next track in queue."""
        if not self.queue:
            print(f"User {self.user_id} queue is empty.")
            return

        next_track_id = self.queue.pop(0)
        await self.save_queue_to_db()

        file_path = await self.get_track_file_path(next_track_id)
        if not file_path:
            print(f"Track {next_track_id} has no file!")
            return

        await self.start_vlc_stream(file_path)
        self.is_playing = True

    async def get_track_file_path(self, track_id: int) -> Optional[str]:
        """Resolve best file path for given track_id."""
        async for session in DBInstance.get_session():
            track = await session.get_one(DBTrack, DBTrack.id == track_id)

            if not track or not track.files:
                return None

            # Auto-pick best file (based on bitrate/codec — here simplified)
            files = track.files
            files = sorted(files, key=lambda f: (f.bitrate or 0), reverse=True)
            return files[0].file_path if files else None

    async def start_vlc_stream(self, file_path: str):
        """Start VLC to stream to user's unique Icecast mount."""
        icecast_url = f"http://{EnvConfig.ICECAST_HOST}:{EnvConfig.ICECAST_PORT}{EnvConfig.ICECAST_MOUNT_TEMPLATE.format(username=self.user_id)}"

        sout = f"#transcode{{acodec=mp3,ab=128}}:std{{access=icecast,mux=mp3,dst={icecast_url}}}"

        if self.current_process:
            self.current_process.terminate()

        print(f"Starting VLC stream for user {self.user_id}: {file_path}")

        self.current_process = subprocess.Popen(["cvlc", "-I", "dummy", file_path, "--sout", sout, "--sout-keep"])

    async def stop(self):
        """Stop VLC process."""
        if self.current_process:
            self.current_process.terminate()
            self.current_process = None
            self.is_playing = False

    async def pause(self):
        """Pausing is not supported in VLC Icecast streaming directly.
        Here, we stop the stream."""
        await self.stop()

    @classmethod
    async def shutdown_all(cls):
        """Stop all VLC streams across all user sessions."""
        for user_id, instance in cls._instances.items():
            if instance.is_playing:
                print(f"Stopping stream for user {user_id}")
                await instance.stop()
        cls._instances.clear()

    async def set_volume(self, level: int):
        if self.current_process:
            self.current_process.stdin.write(f"volume {level}\n".encode())  # type: ignore # example

    async def seek(self, seconds: int):
        # For VLC via `rc` or other IPC, this may look like:
        if self.current_process:
            # This is pseudo: actual implementation may require IPC setup
            self.current_process.stdin.write(f"seek {seconds}\n".encode())


# Helper for GraphQL or FastAPI route
async def get_player_service(user_id: int) -> PlayerService:
    return await PlayerService.get_instance(user_id)
