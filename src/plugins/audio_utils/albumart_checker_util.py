# src/plugins/audioutil/albumart_checker_util.py
from __future__ import annotations

from typing import ClassVar

from sqlmodel import select
from sqlalchemy.orm.strategy_options import selectinload

from core.audioutil_base import AudioUtilBase, register_audioutil
from core.dbmodels import DBFile, DBTrack, DBAlbum, DBAlbumTrack, DBPicture
from Singletons import DBInstance, Logger

logger = Logger()  # singleton


@register_audioutil
class AlbumArtCheckerUtil(AudioUtilBase):
    """Queries the DB for tracks whose albums contain art."""

    name: ClassVar[str] = "albumart_checker"
    description: ClassVar[str] = "Finds DBFiles belonging to tracks with album art."
    version: ClassVar[str] = "2.1.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False
    heavy_io: ClassVar[bool] = False

    async def get_files_with_album_art(self) -> list[DBFile]:
        """
        Returns all DBFile objects that belong to tracks
        whose primary album contains DBPicture entries.
        """
        async for session in DBInstance.get_session():
            result = await session.exec(
                select(DBFile)
                .join(DBTrack, DBFile.track_id == DBTrack.id)
                .join(DBAlbumTrack, DBAlbumTrack.track_id == DBTrack.id)
                .join(DBAlbum, DBAlbumTrack.album_id == DBAlbum.id)
                .join(DBPicture, DBAlbum.id == DBPicture.album_id)
                .options(
                    selectinload(DBFile.track),
                    selectinload(DBFile.track).selectinload(DBTrack.album_tracks),
                )
            )

            rows = result.all()
            await session.close()
            return rows
