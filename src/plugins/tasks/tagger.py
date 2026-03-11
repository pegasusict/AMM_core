from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Iterable, Optional

from sqlmodel import select
from sqlalchemy.orm import selectinload

from core.task_base import TaskBase, register_task
from core.types import DBInterface, TaggerProtocol
from core.enums import TaskType, StageType
from Singletons import DBInstance, Logger
from config import Config
from core.dbmodels import DBTrack, DBAlbumTrack
from core.file_utils import get_file_type


@register_task
class TaggerTask(TaskBase):
    """Writes tags to files using the tagger audioutil."""

    name = "tagger"
    description = "Writes metadata tags to media files."
    version = "2.0.0"
    author = "Mattijs Snepvangers"

    task_type = TaskType.TAGGER
    stage_type = StageType.TAGWRITE
    stage_name = "tagwrite"

    exclusive: ClassVar[bool] = False
    heavy_io: ClassVar[bool] = True

    depends = ["tagger"]

    def __init__(
        self,
        tagger: TaggerProtocol,
        *,
        batch: Optional[Iterable[int]] = None,
        config: Optional[Config] = None,
    ) -> None:
        super().__init__(config=config, batch=batch)
        self.logger = Logger()
        self.config = config or Config.get_sync()
        self.db: DBInterface = DBInstance
        self.tagger = tagger

        self.batch = list(batch or [])
        self._total = len(self.batch)
        self._processed = 0

    async def run(self) -> None:
        async for session in self.db.get_session():
            for track_id in self.batch:
                await self._process_track(session, track_id)

            await session.commit()
            await session.close()

        self.logger.info("Tagger task completed.")

    async def _process_track(self, session: Any, track_id: int) -> None:
        track = await self._load_track(session, track_id)
        if track is None:
            self.logger.warning(f"Tagger: track {track_id} not found")
            return

        resolved = self._resolve_file(track, track_id)
        if resolved is None:
            return
        file, file_path, file_type = resolved

        tags = self._build_tags(track)

        try:
            await self.tagger.set_tags(file_path, file_type[1:], tags)  # strip leading dot
            await self.update_file_stage(file.id, session)
        except Exception as e:
            self.logger.error(f"Tagger failed for {file_path}: {e}")

        self._tick_progress()

    async def _load_track(self, session: Any, track_id: int) -> Optional[DBTrack]:
        result = await session.exec(
            select(DBTrack)
            .where(DBTrack.id == track_id)
            .options(
                selectinload(DBTrack.files),
                selectinload(DBTrack.album_tracks),
            )
        )
        return result.one_or_none()

    def _resolve_file(self, track: DBTrack, track_id: int) -> Optional[tuple[Any, Path, str]]:
        if not track.files:
            self.logger.warning(f"Tagger: track {track_id} has no files")
            return None

        file = track.files[0]
        if not file.file_path:
            self.logger.warning(f"Tagger: file missing path for track {track_id}")
            return None

        file_path = Path(file.file_path)
        file_type = get_file_type(file_path)
        if file_type is None:
            self.logger.warning(f"Tagger: unsupported file type {file_path}")
            return None

        return file, file_path, file_type

    def _build_tags(self, track: DBTrack) -> dict[str, str]:
        performers = getattr(track, "performers", None) or []
        artist = performers[0].full_name if performers else "Unknown Artist"
        title = getattr(track, "title", None)
        if not title and track.files:
            title = track.files[0].file_name

        album_title = "Unknown Album"
        track_number = None
        disc_number = None
        if track.album_tracks:
            album_track = track.album_tracks[0]
            if isinstance(album_track, DBAlbumTrack) and album_track.album:
                album_title = album_track.album.title
            track_number = getattr(album_track, "track_number", None)
            disc_number = getattr(album_track, "disc_number", None)

        tags = {
            "title": title or "Unknown Track",
            "artist": artist,
            "album": album_title,
        }
        if track_number is not None:
            tags["tracknumber"] = str(track_number)
        if disc_number is not None:
            tags["discnumber"] = str(disc_number)

        return tags

    def _tick_progress(self) -> None:
        self._processed += 1
        if self._total:
            self.set_progress(self._processed / self._total)
