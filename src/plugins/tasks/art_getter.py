# -*- coding: utf-8 -*-
#  Copyleft 2021-2025 Mattijs Snepvangers.
#  Part of AMM – Audiophiles' Music Manager

"""Retrieves art from online archives (new plugin system)."""

from pathlib import Path
import urllib.request
import re

from ..exceptions import InvalidURLError
from ..Singletons import Config, Logger, DBInstance
from ..core.enums import TaskType, ArtType, StageType
from ..core.task_base import TaskBase
from ..core.decorators import register_task


def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return url is not None and regex.search(url)


@register_task
class ArtGetter(TaskBase):
    """Retrieves album/artist art from online archives."""

    name = "ArtGetter"
    description = "Retrieves art from online archives."
    version = "2.0"
    task_type = TaskType.ART_GETTER
    stage_type = StageType.ART_RETRIEVED

    # Dependency injection: unified system resolves this automatically
    depends = ["MusicBrainzClient"]

    def __init__(self, batch: dict[str, ArtType], config: Config, MusicBrainzClient):
        super().__init__(config=config)
        self.batch = batch
        self.logger = Logger(config)
        self.art_path = config.get_path("art")
        self.db = DBInstance
        self.mbc = MusicBrainzClient

        self._total = len(batch)
        self._processed = 0

    # -----------------------------------------------------
    # Async task entry point
    # -----------------------------------------------------
    async def run(self):
        self.logger.info("Running ArtGetter task")

        # Iterate correctly (old code used `for x,y in dict` which is wrong)
        for mbid, art_type in self.batch.items():
            await self.get_art(mbid, art_type)
            self.set_progress(self._processed / self._total)

        self.logger.info("ArtGetter task completed")
        self.set_completed("Art retrieval complete")

    # -----------------------------------------------------
    async def get_art(self, mbid: str, art_type: ArtType):
        self.logger.info(f"Retrieving {art_type.name} art for {mbid}")

        url = self.mbc.get_art(mbid)
        if not url:
            self.logger.warning(f"No art found for MBID {mbid}")
            self._processed += 1
            return

        await self.save_art(url, mbid, art_type)

        self._processed += 1

    # -----------------------------------------------------
    async def save_art(self, url: str, mbid: str, art_type: ArtType):
        if not url:
            self.logger.warning(f"No URL provided for MBID {mbid}")
            return

        if not is_valid_url(url):
            raise InvalidURLError(f"Invalid URL: {url}")

        save_path = Path(self.art_path) / f"{mbid}.jpg"

        self.logger.info(f"Downloading {art_type.name.lower()} art: {url}")

        # Blocking download is fine — offloaded via task system
        urllib.request.urlretrieve(url, save_path)

        await self.db.register_picture(mbid, art_type, save_path)

        self.logger.info(f"Art saved to {save_path}")
