# audioutils/dedupe.py
from __future__ import annotations
from typing import ClassVar, List, Dict, Any

from ..core.audioutil_base import AudioUtilBase, register_audioutil
from ..core.enums import CodecPriority
from ..Singletons import Logger

logger = Logger  # singleton


@register_audioutil
class DedupeUtil(AudioUtilBase):
    """
    AudioUtil that compares a list of file objects and decides which one
    should be kept based on codec priority and bitrate.
    """

    # --- Plugin metadata ---
    name: ClassVar[str] = "dedupe"
    description: ClassVar[str] = "Determines best-quality file and marks others for deletion."
    version: ClassVar[str] = "1.1.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    depends: ClassVar[List[str]] = []   # standalone util
    exclusive: ClassVar[bool] = False   # safe to run in parallel
    heavy_io: ClassVar[bool] = False    # CPU-light

    def __init__(self):
        self.logger = Logger

    async def dedupe_files(self, files: list) -> Dict[str, Any]:
        """
        Given a list of file objects, returns:
            {
                "keep": file,
                "delete": [file, file, ...]
            }

        Highest quality = highest CodecPriority + highest bitrate.
        """
        if not files:
            return {"keep": None, "delete": []}

        if len(files) == 1:
            return {"keep": files[0], "delete": []}

        try:
            sorted_files = sorted(
                files,
                key=lambda f: (CodecPriority[f.codec], f.bitrate),
                reverse=True,
            )
        except Exception as e:
            self.logger.error(f"Failed to dedupe files: {e}")
            raise

        keep = sorted_files[0]
        delete = sorted_files[1:]

        self.logger.debug(
            f"Dedupe: keeping {keep.path if hasattr(keep, 'path') else keep}, "
            f"deleting {len(delete)} alternatives"
        )

        return {"keep": keep, "delete": delete}
