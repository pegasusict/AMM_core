from __future__ import annotations
from pathlib import Path
from typing import Any, ClassVar, Dict

from core.audioutil_base import AudioUtilBase, register_audioutil
from core.exceptions import FileError
from Singletons import Logger
from core.file_utils import get_file_type
from config import Config

from .tagger import Tagger
from .media_parser import MediaParser
from .acoustid import AcoustID
from .utils.acoustidhttpclient import AcoustIDHttpClient


logger = Logger()  # singleton logger instance


@register_audioutil
class FingerprintFile(AudioUtilBase):
    """
    Performs AcoustID fingerprint extraction and returns raw metadata.
    """

    # --- Metadata required by PluginBase ---
    name: ClassVar[str] = "fingerprint_file"
    description: ClassVar[str] = "Extracts AcoustID fingerprint and acoustical metadata from a file."
    version: ClassVar[str] = "1.1.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    # Audio fingerprinting does heavy I/O and CPU
    exclusive: ClassVar[bool] = False         # safe to run in parallel
    heavy_io: ClassVar[bool] = True           # disk + CPU intensive

    def __init__(self, config: Config | None = None) -> None:
        super().__init__(config=config)
        self.logger = Logger()

    async def run(self, path: Path) -> Dict[str, Any]:
        file_type = get_file_type(path)
        if file_type is None:
            raise FileError(f"fingerprint_file: illegal filetype: {path}")

        acoustid = AcoustID(
            tagger=Tagger(),
            media_parser=MediaParser(),
            acoustid_client=AcoustIDHttpClient(),
        )

        try:
            return await acoustid.process(path)
        except Exception as e:
            self.logger.error(f"{self.name}: fingerprinting failed — {e}")
            raise
