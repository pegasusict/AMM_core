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
import urllib.request
            
from .Task import Task, TaskType, TaskStatus
from ..Singletons.config import Config
from ..Singletons.Logger import Logger
from ..Singletons.DB import DB
from ..Clients.MB_Client import MusicBrainzClient as mbc

class ArtType(Enum):
    """
    Enum for different types of art.
    """
    ALBUM = "album"
    ARTIST = "artist"

class ArtGetter(Task):
    """
    This class retrieves art from online archives.
    """

    def __init__(self, batch:dict, config:Config):
        """
        Initializes the ArtGetter class.

        Args:
            config: The configuration object.
        """
        super().__init__(config, task_name="ArtGetter", task_type=TaskType.ART_GETTER)
        self.batch = batch
        self.config = config
        self.art_path = self.config.get("paths","base")+self.config.get("paths","art")+"/"
        self.processed=0

    def run(self) -> None:
        """
        Runs the ArtGetter task.
        """
        Logger.info("Running ArtGetter task")
        for mbid, art_type in self.batch:
            if art_type == ArtType.ALBUM:
                self.get_album_art(mbid)
            elif art_type == ArtType.ARTIST:
                self.get_artist_art(mbid)
            else:
                Logger.warning(f"Unknown art type: {art_type}")
        Logger.info("ArtGetter task completed")
        self.set_task_result("Art retrieval completed")
        self.task_finished()

    def get_album_art(self, mbid:str) -> None:
        """
        Retrieves album art for the given item.

        Args:
            item: The item to retrieve album art for.
        """
        Logger.info(f"Retrieving album art for MBID {mbid}")
        url = mbc.get_album_art(mbid)
        if url:
            Logger.info(f"Album art URL: {url}")
        else:
            Logger.warning(f"No album art found for MBID {mbid}")
        self.processed += 1
        self.task_progress = (self.processed / len(self.batch)) * 100
        Logger.info(f"Progress: {self.task_progress:.2f}%")

    def get_artist_art(self, mbid:str) -> None:
        """
        Retrieves artist art for the given item.

        Args:
            item: The item to retrieve artist art for.
        """
        Logger.info(f"Retrieving artist art for MBID {mbid}")
        url = mbc.get_artist_art(mbid)
        if url:
            Logger.info(f"Artist art URL: {url}")
        else:
            Logger.warning(f"No artist art found for MBID {mbid}")
        self.processed += 1
        self.task_progress = (self.processed / len(self.batch)) * 100
        Logger.info(f"Progress: {self.task_progress:.2f}%")

    async def save_art(self, url:str, mbid:str, art_type:ArtType) -> None:
        """
        Saves the retrieved art to the local filesystem.

        Args:
            url: The URL of the art.
            mbid: The MBID of the item.
            art_type: The type of art (album or artist).
        """
        if url is None:
            Logger.warning(f"No URL provided for MBID {mbid}")
            return
        if mbid is None:
            Logger.warning(f"No MBID provided for URL {url}")
            return
        if art_type == ArtType.ALBUM:
            Logger.info(f"Saving album art for MBID {mbid}")
        elif art_type == ArtType.ARTIST:
            Logger.info(f"Saving artist art for MBID {mbid}")
        else:
            Logger.warning(f"Unknown art type: {art_type}")
            return
        save_path = f"{self.art_path}{mbid}.jpg"
        urllib.request.urlretrieve(url, save_path)
        DB.register_picture(mbid, art_type, save_path)
        Logger.info(f"Art saved to {save_path}")