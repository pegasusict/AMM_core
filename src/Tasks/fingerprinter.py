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

"""Fingerprinter Task."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session
from pydantic import ValidationError

from ..dbmodels import DBFile, DBPerson, DBTrack
from ..enums import TaskType, Stage
from task import Task
from Singletons import Config, DB, Logger
from AudioUtils.acoustid import AcoustID
from ..models import MetadataModel

from AudioUtils.utils.acoustidhttpclient import AcoustIDHttpClient
from AudioUtils.utils.durationparser import DurationParser
from AudioUtils.utils.simpletagger import SimpleTagger


class FingerPrinter(Task):
    """Task that fingerprints and identifies audio files via AcoustID."""

    batch: List[int]

    def __init__(self, config: Config, batch: List[int]) -> None:
        super().__init__(config=config, task_type=TaskType.FINGERPRINTER)
        self.config: Config = config
        self.batch: List[int] = batch  # type: ignore
        self.db: DB = DB()
        self.logger: Logger = Logger(config)
        self.stage: Stage = Stage.FINGERPRINTED

    async def run(self) -> None:
        """Runs the fingerprinting task asynchronously."""
        session: Session = self.db.get_session()
        for file_id in self.batch:
            await self._process_file_and_update(session, file_id)
        session.commit()
        session.close()

    async def _process_file_and_update(self, session: Session, file_id: int) -> None:
        try:
            file: DBFile = self._get_file(session, file_id)
            if not self._file_exists(file.file_path):
                return
            raw_metadata: Dict[str, Any] = await self.process_file(Path(file.file_path))
            metadata: MetadataModel = self._validate_metadata(raw_metadata)

            track: DBTrack = self._update_track(session, file)
            self._update_artists(session, track, metadata)
            self._update_track_info(track, metadata)

            session.add(file)
            session.add(track)
            self.update_file_stage(file.id, session)
            self.set_progress()
        except Exception as e:
            self.logger.error(f"Error processing file {file_id}: {e}")

    def _get_file(self, session: Session, file_id: int) -> DBFile:
        return session.get_one(DBFile, id == file_id)

    def _file_exists(self, file_path: str) -> bool:
        path: Path = Path(file_path)
        if not path.exists():
            self.logger.error(f"File {path} does not exist.")
            return False
        return True

    def _update_track(self, session: Session, file: DBFile) -> DBTrack:
        if file.track is None:
            track: DBTrack = DBTrack(files=[file])
            session.add(track)
            session.commit()
            track = session.refresh(track)
        else:
            track = session.get_one(DBTrack, DBTrack.id == file.track_id)
            file.track = track
            file.track_id = track.id
        return track

    def _update_artists(self, session: Session, track: DBTrack, metadata: MetadataModel) -> None:
        for artist in metadata.artists:
            db_artist: Optional[DBPerson] = session.get_one(
                DBPerson, DBPerson.full_name == artist.name
            )
            if db_artist is None:
                db_artist = DBPerson(full_name=artist.name, mbid=artist.mbid)
                session.add(db_artist)
                session.commit()
                db_artist = session.refresh(db_artist)
            if db_artist is not None and db_artist not in track.performers:
                track.performers.append(db_artist)

    def _update_track_info(self, track: DBTrack, metadata: MetadataModel) -> None:
        if track.title == "" and metadata.title is not None:
            track.title = metadata.title
        if track.mbid == "" and metadata.mbid is not None:
            track.mbid = metadata.mbid

    def _validate_metadata(self, metadata: Dict[str, Any]) -> MetadataModel:
        """Validate and parse metadata using Pydantic models."""
        try:
            return MetadataModel(**metadata)
        except ValidationError as e:
            self.logger.warning(f"Invalid metadata format: {e}")
            return MetadataModel()

    async def process_file(self, path: Path) -> Dict[str, Union[str, None]]:
        """Fingerprints and looks up metadata for a single file."""
        acoustid: AcoustID = AcoustID(
            path=path,
            acoustid_client=AcoustIDHttpClient(),
            tagger=SimpleTagger(path),
            parser=DurationParser(),
            logger=self.logger,
        )
        return await acoustid.process()
