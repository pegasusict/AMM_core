# -*- coding: utf-8 -*-
#  Copyleft 2021-2025 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  Licensed under GPLv3 or later.

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from ..core.enums import TaskType, StageType, PluginType
from ..core.task_base import TaskBase
from ..core.decorators import register_task
from ..Singletons import Config, DBInstance, Logger
from ..core.dbmodels import DBFile, DBPerson, DBTrack


@register_task
class FingerPrinter(TaskBase):
    """
    Fingerprints audio files using AcoustID and updates DB metadata.
    Uses registry-based audioutils:
      - fingerprint_file
      - validate_fingerprint_metadata
      - extract_fp_entities
    """

    name: str = "FingerPrinter"
    plugin_type: PluginType = PluginType.TASK
    task_type: TaskType = TaskType.FINGERPRINTER
    stage_type: StageType = StageType.FINGERPRINTED
    description: str = "Identifies audio files using AcoustID and enriches metadata."
    depends = ["fingerprint_file", "validate_fingerprint_metadata", "extract_fp_entities"]

    def __init__(self, config: Config, batch: List[int]) -> None:
        super().__init__(config=config, task_type=TaskType.FINGERPRINTER)
        self.config = config
        self.batch = batch  # type: ignore
        self.db = DBInstance
        self.logger = Logger(config)

    async def run(self) -> None:
        async for session in self.db.get_session():
            for file_id in self.batch:
                await self._process_one(session, file_id)
                self.set_progress()
            await session.commit()
            await session.close()

    async def _process_one(self, session, file_id: int) -> None:
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

            # 1. Fingerprint raw metadata
            raw = await self.call("fingerprint_file", path)

            # 2. Validate / normalize
            metadata = await self.call("validate_fingerprint_metadata", raw)

            # 3. Extract entities used by the task
            entities = await self.call("extract_fp_entities", metadata)

            # -------------------------
            # DATABASE UPDATE SECTION
            # -------------------------

            track = await self._update_track(session, file)
            await self._update_artists(session, track, entities["artists"])
            self._update_track_info(track, entities)

            session.add(track)
            session.add(file)

            self.update_file_stage(file.id, session)

        except Exception as e:
            self.logger.error(f"Fingerprint error for file {file_id}: {e}")

    async def _load_file(self, session, file_id: int) -> DBFile | None:
        file = await session.get_one(DBFile, DBFile.id == file_id)
        if file is None:
            self.logger.error(f"DBFile {file_id} not found")
        return file

    async def _update_track(self, session: Session, file: DBFile) -> DBTrack:
        """Ensure a DBTrack exists for this DBFile."""
        if file.track is None:
            track = DBTrack(files=[file])
            session.add(track)
            await session.commit()
            await session.refresh(track)
        else:
            track = await session.get_one(DBTrack, DBTrack.id == file.track_id)
            file.track_id = track.id
            file.track = track
        return track

    async def _update_artists(self, session: Session, track: DBTrack, artists: List[Dict[str, str]]) -> None:
        """Create missing DBPerson entries and attach to track.performers."""
        for a in artists:
            name = a.get("name")
            mbid = a.get("mbid")

            db_artist = await session.get_one(DBPerson, DBPerson.full_name == name)
            if db_artist is None:
                db_artist = DBPerson(full_name=name, mbid=mbid)
                session.add(db_artist)
                await session.commit()
                await session.refresh(db_artist)

            if db_artist not in track.performers:
                track.performers.append(db_artist)

    def _update_track_info(self, track: DBTrack, entities: Dict[str, Any]) -> None:
        """Update title + MBID only if missing."""
        if track.title == "" and entities.get("title"):
            track.title = entities["title"]
        if track.mbid == "" and entities.get("mbid"):
            track.mbid = entities["mbid"]
