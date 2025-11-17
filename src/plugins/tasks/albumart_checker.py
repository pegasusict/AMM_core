# -*- coding: utf-8 -*-
"""Task that updates stages for files whose albums have art."""

from ..core.task_base import TaskBase
from ..core.enums import StageType, TaskType
from ..core.decorators import register_task
from ..Singletons import Logger


@register_task
class AlbumArtChecker(TaskBase):
    """
    Uses AlbumArtCheckerUtil to detect files whose albums contain art
    and updates their stage.
    """

    name = "AlbumArtChecker"
    description = "Checks DB for album art and updates file stages."
    version = "2.0.0"
    task_type = TaskType.ART_CHECKER
    stage_type = StageType.ANALYSE

    # Util injection
    depends = ["AlbumArtCheckerUtil"]

    def __init__(self, config, AlbumArtCheckerUtil):
        super().__init__(config=config)
        self.logger = Logger(config)
        self.util = AlbumArtCheckerUtil

    async def run(self):
        self.logger.info("Running AlbumArtChecker")

        files = await self.util.get_files_with_album_art()
        total = len(files)

        async for session in self.db.get_session():
            for i, file in enumerate(files):
                self.update_file_stage(file.id, session)
                self.set_progress((i + 1) / total)

            await session.commit()
            await session.close()

        self.set_completed("Album art analysis completed")
