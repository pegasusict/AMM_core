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

import urllib.request
import re

from ..Exceptions import InvalidURLError
from task import Task, TaskStatus
from Enums import TaskType, ArtType
from Singletons.config import Config
from Singletons.logger import Logger
from Singletons.database import DB
from Clients.mb_client import MusicBrainzClient as mbclient


def is_valid_url(url):
    regex = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return url is not None and regex.search(url)


class ArtGetter(Task):
    """
    This class retrieves art from online archives.
    """

    def __init__(self, batch: dict[str, ArtType], config: Config):
        """
        Initializes the ArtGetter class.

        Args:
            config: The configuration object.
        """
        super().__init__(config, task_type=TaskType.ART_GETTER)
        self.batch = batch  # type: ignore
        self.config = config
        self.art_path = self.config.get("paths", "art")
        self.processed = 0
        self.logger = Logger(config)
        self.mbc = mbclient(config)
        self.database = DB()

    def run(self) -> None:
        """
        Runs the ArtGetter task.
        """
        self.logger.info("Running ArtGetter task")
        for mbid, art_type in self.batch:  # type: ignore
            _ = self.get_art(mbid, ArtType(art_type))
        self.logger.info("ArtGetter task completed")
        self.result = "Art retrieval completed"
        self.status = TaskStatus.COMPLETED
        self.progress = 100.0
        self.logger.info(f"Task completed in {self.duration:.2f} seconds")
        self.logger.info(f"Total items processed: {self.processed}")

    async def get_art(self, mbid: str, art_type: ArtType) -> None:
        """
        Retrieves album/artist art for the given item.

        Args:
            mbid:       (str)       The item to retrieve album/artist art for.
            art_type:   (ArtType)   The ArtType requested
        """
        self.logger.info(f"Retrieving {art_type} art for MBID {mbid}")
        url = self.mbc.get_art(mbid)
        if url:
            self.logger.info(f"{art_type} art URL: {url}")
            await self.save_art(url, mbid, art_type)
        else:
            self.logger.warning(f"No artist art found for MBID {mbid}")
        self.processed += 1
        self.progress = (self.processed / len(self.batch)) * 100
        self.logger.info(f"Progress: {self.progress:.2f}%")

    async def save_art(self, url: str, mbid: str, art_type: ArtType) -> None:
        """
        Saves the retrieved art to the local filesystem.

        Args:
            url: The URL of the art.
            mbid: The MBID of the item.
            art_type: The type of art (album or artist).
        """
        if url is None:
            self.logger.warning(f"No URL provided for MBID {mbid}")
            return
        if mbid is None:
            self.logger.warning(f"No MBID provided for URL {url}")
            return
        if art_type == ArtType.ALBUM:
            self.logger.info(f"Saving album art for MBID {mbid}")
        elif art_type == ArtType.ARTIST:
            self.logger.info(f"Saving artist art for MBID {mbid}")
        else:
            self.logger.warning(f"Unknown art type: {art_type}")
            return
        save_path = f"{self.art_path}{mbid}.jpg"

        if not is_valid_url(url):
            raise InvalidURLError("Invalid url found.")
        urllib.request.urlretrieve(url, save_path)
        self.database.register_picture(mbid, art_type.value, save_path)
        self.logger.info(f"Art saved to {save_path}")
