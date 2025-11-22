from __future__ import annotations
from typing import Dict, Any, ClassVar

from ..core.audioutil_base import AudioUtilBase, register_audioutil
from ..Singletons import Logger
from ..models import MetadataModel


logger = Logger  # singleton logger instance


@register_audioutil
class ExtractFingerprintEntities(AudioUtilBase):
    """
    Normalizes artist + track metadata for fingerprint-processing tasks.
    """

    # --- Plugin metadata ---
    name: ClassVar[str] = "extract_fp_entities"
    description: ClassVar[str] = "Extracts normalized track + artist metadata for fingerprint tasks."
    version: ClassVar[str] = "1.1.1"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False     # safe to run in parallel
    heavy_io: ClassVar[bool] = False      # very lightweight CPU work

    def __init__(self):
        self.logger = Logger

    async def run(self, metadata: MetadataModel) -> Dict[str, Any]:
        """
        Convert MetadataModel → simple dictionary for downstream tasks.
        """
        try:
            return {
                "artists": [
                    {"name": a.name, "mbid": a.mbid}
                    for a in metadata.artists
                ],
                "title": metadata.title,
                "mbid": metadata.mbid,
            }
        except Exception as e:
            self.logger.error(f"{self.name}: failed to extract entities — {e}")
            raise
