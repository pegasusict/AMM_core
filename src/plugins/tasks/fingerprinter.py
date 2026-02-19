from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Dict, List

from sqlmodel import select

from core.enums import TaskType, StageType, PluginType
from core.task_base import TaskBase, register_task
from core.types import (
    AsyncSessionLike,
    DBInterface,
    ExtractFPEntitiesProtocol,
    FingerprintFileProtocol,
    ValidateFingerprintMetadataProtocol,
)
from config import Config
from Singletons import DBInstance, Logger
from core.dbmodels import DBFile, DBPerson, DBTrack


@register_task
class FingerPrinter(TaskBase):
    """
    Fingerprints audio files using AcoustID and updates DB metadata.
    Uses registry-injected utils:
      - fingerprint_file
      - validate_fingerprint_metadata
      - extract_fp_entities
    """

    name = "FingerPrinter"
    description = "Identifies audio files using AcoustID and enriches metadata."
    version = "2.0.0"
    author = "Mattijs Snepvangers"

    plugin_type = PluginType.TASK
    task_type = TaskType.FINGERPRINTER
    stage_type = StageType.ANALYSE
    stage_name = "analyse"

    # required in new spec
    exclusive: ClassVar[bool] = False       # non-exclusive, can run in parallel
    heavy_io: ClassVar[bool] = True         # disk access + DB writes

    depends = [
        "fingerprint_file",
        "validate_fingerprint_metadata",
        "extract_fp_entities",
    ]

    def __init__(
        self,
        fingerprint_file: FingerprintFileProtocol,
        validate_fingerprint_metadata: ValidateFingerprintMetadataProtocol,
        extract_fp_entities: ExtractFPEntitiesProtocol,
        *,
        batch: List[int],
    ) -> None:
        self.logger = Logger()
        self.config = Config.get_sync()
        self.batch = batch

        # injected utils
        self.fp_file = fingerprint_file
        self.validate = validate_fingerprint_metadata
        self.extract = extract_fp_entities

        self.db: DBInterface = DBInstance

        self._total = len(batch)
        self._processed = 0

    # ---------------------------------------------------------
    async def run(self) -> None:
        self.logger.info(f"FingerPrinter: processing {self._total} files")

        async for session in self.db.get_session():
            for file_id in self.batch:
                await self._process_one(session, file_id)
                self._processed += 1
                self.set_progress(self._processed / self._total)

            await session.commit()
            await session.close()

        self.set_completed("Fingerprinting completed.")

    # ---------------------------------------------------------
    async def _process_one(self, session: AsyncSessionLike, file_id: int) -> None:
        try:
            file = await self._load_file(session, file_id)
            if file is None:
                return

            path = Path(file.file_path)
            if not path.exists():
                self.logger.error(f"File does not exist: {path}")
                return

            # -------------------------
            # AUDIOUTIL PIPELINE
            # -------------------------
            raw = await self.fp_file(path)
            metadata = await self.validate(raw)
            entities = await self.extract(metadata)

            # -------------------------
            # DATABASE UPDATE
            # -------------------------
            track = await self._update_track(session, file)
            await self._update_artists(session, track, entities["artists"])
            self._update_track_info(track, entities)

            session.add(track)
            session.add(file)

            await self.update_file_stage(file.id, session)

        except Exception as e:
            self.logger.error(f"Fingerprint error for file {file_id}: {e}")

    # ---------------------------------------------------------
    async def _load_file(self, session: AsyncSessionLike, file_id: int) -> DBFile | None:
        file = await session.get(DBFile, file_id)
        if file is None:
            self.logger.error(f"DBFile {file_id} not found")
        return file

    # ---------------------------------------------------------
    async def _update_track(self, session: AsyncSessionLike, file: DBFile) -> DBTrack:
        """Ensure a DBTrack exists for this DBFile."""
        if file.track_id is None:
            track = DBTrack(files=[file])
            session.add(track)
            await session.commit()
            await session.refresh(track)
            file.track_id = track.id
            return track

        track = await session.get(DBTrack, file.track_id)
        if track is None:
            # orphan fix
            track = DBTrack(files=[file])
            session.add(track)
            await session.commit()
            await session.refresh(track)
        return track

    # ---------------------------------------------------------
    async def _update_artists(
        self,
        session: AsyncSessionLike,
        track: DBTrack,
        artists: List[Dict[str, str]],
    ) -> None:
        """Create missing DBPerson entries and attach to track.performers."""
        for a in artists:
            name = a.get("name")
            mbid = a.get("mbid")

            # find by name
            result = await session.exec(
                select(DBPerson).where(DBPerson.full_name == name)
            )
            db_artist = result.one_or_none()

            if db_artist is None:
                db_artist = DBPerson(full_name=name, mbid=mbid)
                session.add(db_artist)
                await session.commit()
                await session.refresh(db_artist)

            if db_artist not in track.performers:
                track.performers.append(db_artist)

    # ---------------------------------------------------------
    def _update_track_info(self, track: DBTrack, entities: Dict[str, Any]) -> None:
        """Set track.title/mbid only if missing."""
        title = entities.get("title")
        mbid = entities.get("mbid")

        if not track.title and title:
            track.title = title

        if (not track.mbid or str(track.mbid).startswith("local_")) and mbid:
            track.mbid = mbid
