from __future__ import annotations

from pathlib import Path
import urllib.request
import re
from typing import ClassVar

from core.exceptions import InvalidURLError
from Singletons import Logger, DBInstance
from config import Config
from core.enums import TaskType, ArtType, StageType
from core.task_base import TaskBase
from core.types import DBInterface, MusicBrainzClientProtocol
from core.task_base import register_task


def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r"^https?://"                      # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(url and regex.search(url))


@register_task
class ArtGetter(TaskBase):
    """
    Retrieves album/artist art and writes it to disk.
    """

    name = "art_getter"
    description = "Retrieves album and artist art from online archives."
    version = "2.0.0"
    author = "Mattijs Snepvangers"
    task_type = TaskType.ART_GETTER
    stage_type = StageType.METADATA
    stage_name = "metadata"

    # MUST be present:
    exclusive: ClassVar[bool] = False         # can run concurrently
    heavy_io: ClassVar[bool] = True           # downloads + filesystem writes

    depends = ["MusicBrainzClient"]

    def __init__(
        self,
        batch: dict[str, ArtType],
        config: Config,
        MusicBrainzClient: MusicBrainzClientProtocol,
    ) -> None:
        self.logger = Logger()
        self.batch = batch
        self.config = config
        self.db: DBInterface = DBInstance
        self.mbc = MusicBrainzClient

        self.art_path = self.config.get_path("art")

        self._total = len(batch)
        self._processed = 0

    # -----------------------------------------------
    async def run(self) -> None:
        self.logger.info("Running ArtGetter task")

        for mbid, art_type in self.batch.items():
            await self.get_art(mbid, art_type)
            self.set_progress(self._processed / self._total)

        self.logger.info("ArtGetter task completed")
        self.set_completed("Art retrieval complete")

    # -----------------------------------------------
    async def get_art(self, mbid: str, art_type: ArtType) -> None:
        self.logger.info(f"Retrieving {art_type.name} art for {mbid}")

        url = await self.mbc.get_art(mbid)
        if not url:
            self.logger.warning(f"No art found for MBID {mbid}")
            self._processed += 1
            return

        await self.save_art(url, mbid, art_type)
        self._processed += 1

    # -----------------------------------------------
    async def save_art(self, url: str, mbid: str, art_type: ArtType) -> None:
        if not is_valid_url(url):
            raise InvalidURLError(f"Invalid URL: {url}")

        save_path = Path(self.art_path) / f"{mbid}.jpg"

        self.logger.info(f"Downloading {art_type.name.lower()} art: {url}")

        # Heavy I/O — TaskManager handles thread offloading
        urllib.request.urlretrieve(url, save_path)

        await self.db.register_picture(mbid, art_type, save_path)

        self.logger.info(f"Art saved to {save_path}")
