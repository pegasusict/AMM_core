from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import ClassVar, Iterable, Optional, Tuple

from sqlmodel import select
from sqlalchemy.orm import selectinload

from core.task_base import TaskBase, register_task
from core.types import AsyncSessionLike, DBInterface
from core.enums import TaskType, StageType
from Singletons import DBInstance, Logger
from config import Config
from dbmodels import DBTrack, DBAlbumTrack


@register_task
class SorterTask(TaskBase):
    """Sorts files into the music library tree based on basic metadata."""

    name = "sorter"
    description = "Sorts files into the library directory structure."
    version = "2.0.0"
    author = "Mattijs Snepvangers"

    task_type = TaskType.SORTER
    stage_type = StageType.SORT
    stage_name = "sort"

    exclusive: ClassVar[bool] = False
    heavy_io: ClassVar[bool] = True

    depends = []

    def __init__(
        self,
        *,
        batch: Optional[Iterable[int]] = None,
        config: Optional[Config] = None,
    ) -> None:
        self.logger = Logger()
        self.config = config or Config.get_sync()
        self.db: DBInterface = DBInstance

        self.batch = list(batch or [])
        self._total = len(self.batch)
        self._processed = 0

    async def run(self) -> None:
        async for session in self.db.get_session():
            for track_id in self.batch:
                track = await self._load_track(session, track_id)
                if track is None or not track.files:
                    continue

                file = track.files[0]
                if not file.file_path:
                    continue

                input_path = Path(file.file_path)
                if not input_path.exists():
                    self.logger.warning(f"Sorter: input missing {input_path}")
                    continue

                metadata = self._build_metadata(track)
                target_path = self._build_target_path(metadata)

                if target_path.exists():
                    self.logger.warning(f"Sorter: target exists {target_path}")
                    continue

                try:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    input_path.rename(target_path)
                    await self.update_file_stage(file.id, session)
                except Exception as e:
                    self.logger.error(f"Sorter failed for {input_path}: {e}")

                self._processed += 1
                if self._total:
                    self.set_progress(self._processed / self._total)

            await session.commit()
            await session.close()

        self.logger.info("Sorter task completed.")

    async def _load_track(self, session: AsyncSessionLike, track_id: int) -> Optional[DBTrack]:
        result = await session.exec(
            select(DBTrack)
            .where(DBTrack.id == track_id)
            .options(
                selectinload(DBTrack.files),
                selectinload(DBTrack.performers),
                selectinload(DBTrack.album_tracks),
            )
        )
        return result.one_or_none()

    def _build_metadata(self, track: DBTrack) -> dict:
        album_title = "[compilations]"
        year = "0000"
        disc_number = "1"
        track_number = "1"

        if track.album_tracks:
            album_track = track.album_tracks[0]
            if isinstance(album_track, DBAlbumTrack) and album_track.album:
                album_title = album_track.album.title or album_title
                if album_track.album.release_date:
                    year = str(album_track.album.release_date.year)
            if album_track.track_number:
                track_number = str(album_track.track_number)
            if album_track.disc_number:
                disc_number = str(album_track.disc_number)

        artist = track.performers[0].full_name if track.performers else "Unknown Artist"

        return {
            "album": album_title,
            "artist_sort": artist,
            "title": track.title or "Unknown Track",
            "year": year,
            "disc_number": disc_number,
            "track_number": track_number,
        }

    def _build_target_path(self, metadata: dict) -> Path:
        base_path = Path(self.config.get_path("base"))

        album = self._clean_string(str(metadata.get("album", "[compilations]")))
        artist_sort = self._clean_string(str(metadata.get("artist_sort", "[Unknown Artist]")))
        track_title = self._clean_string(str(metadata.get("title", "[Unknown Track]")))
        year = str(metadata.get("year", "0000"))

        initial = self._create_index_symbol(artist_sort)
        disc_number = self._format_number(str(metadata.get("disc_number", "1")), "1")
        track_number = self._format_number(str(metadata.get("track_number", "1")), "1")

        target_dir = base_path / initial / artist_sort / f"({year}) - {album}"
        target_file = f"{disc_number}{track_number} {artist_sort} - {track_title}.mp3"

        return target_dir / self._clean_string(target_file)

    def _create_index_symbol(self, artist_sort: str) -> str:
        initial = artist_sort[0].upper() if artist_sort else "#"
        norm_initial = unicodedata.normalize("NFD", initial)
        initial = "".join(char for char in norm_initial if unicodedata.category(char) != "Mn")
        return initial if initial.isascii() and initial.isalpha() else "0-9"

    def _format_number(self, number: str, count: str) -> str:
        return "" if int(count) == 1 else f"{number.zfill(len(count))}."

    def _clean_string(self, string: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', "-", string).strip()
