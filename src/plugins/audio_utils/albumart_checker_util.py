# -*- coding: utf-8 -*-
"""Audio util that checks DB for tracks whose albums contain art."""

from sqlmodel import select
from sqlalchemy.orm.strategy_options import selectinload

from ..core.audioutil_base import AudioUtilBase
from ..core.dbmodels import DBFile, DBTrack, DBAlbum, DBAlbumTrack, DBPicture
from ..core.decorators import register_audioutil
from ..Singletons import DBInstance


@register_audioutil()
class AlbumArtCheckerUtil(AudioUtilBase):
    """Queries the DB for files whose primary album contains art."""

    name = "AlbumArtCheckerUtil"
    description = "Finds DBFiles belonging to tracks with album art."
    version = "2.0.0"
    depends = []

    async def get_files_with_album_art(self):
        """
        Returns all DBFile objects that belong to tracks
        whose primary album contains DBPicture entries.
        """
        async for session in DBInstance.get_session():
            result = session.exec(
                select(DBFile)
                .join(DBTrack, DBFile.track_id == DBTrack.id)
                .join(DBAlbumTrack, DBAlbumTrack.track_id == DBTrack.id)
                .join(DBAlbum, DBAlbumTrack.album_id == DBAlbum.id)
                .join(DBPicture, DBAlbum.id == DBPicture.album_id)
                .options(
                    selectinload(DBFile.track),
                    selectinload(DBFile.track).selectinload(DBTrack.album_tracks),
                )
            ).all()

            await session.close()
            return result
