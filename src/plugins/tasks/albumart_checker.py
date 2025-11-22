from __future__ import annotations

from ..core.task_base import TaskBase, register_task
from ..core.enums import StageType, TaskType
from ..Singletons import Logger


@register_task()
class AlbumArtChecker(TaskBase):
    """
    Uses AlbumArtCheckerUtil to detect files whose albums contain art
    and updates their stage.
    """

    name = "album_art_checker"
    description = "Checks DB for album art and updates file stages."
    version = "2.0.0"
    task_type = TaskType.ART_CHECKER
    stage_type = StageType.ANALYSE

    depends = ["AlbumArtCheckerUtil"]
    exclusive = False
    heavy_io = False

    def __init__(self, AlbumArtCheckerUtil):
        self.logger = Logger()
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
