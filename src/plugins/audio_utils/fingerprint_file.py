from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, ClassVar

from ..core.audioutil_base import AudioUtilBase, register_audioutil
from ..core.exceptions import FileError
from ..Singletons import Logger

from ..AudioUtils import Tagger, get_file_type, MediaParser, AcoustID
from ..AudioUtils.utils.acoustidhttpclient import AcoustIDHttpClient


logger = Logger  # singleton logger instance


@register_audioutil
class FingerprintFile(AudioUtilBase):
    """
    Performs AcoustID fingerprint extraction and returns raw metadata.
    """

    # --- Metadata required by PluginBase ---
    name: ClassVar[str] = "fingerprint_file"
    description: ClassVar[str] = "Extracts AcoustID fingerprint + acoustical metadata from a file."
    version: ClassVar[str] = "1.1.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    # Audio fingerprinting does heavy I/O and CPU
    exclusive: ClassVar[bool] = False         # safe to run in parallel
    heavy_io: ClassVar[bool] = True           # disk + CPU intensive

    def __init__(self, config=None):
        super().__init__(config=config)
        self.logger = Logger

    async def run(self, path: Path) -> Dict[str, Any]:
        file_type = get_file_type(path)
        if file_type is None:
            raise FileError(f"fingerprint_file: illegal filetype: {path}")

        acoustid = AcoustID(
            path=path,
            acoustid_client=AcoustIDHttpClient(),
            tagger=Tagger(path, file_type),
            parser=MediaParser(),
            logger=self.logger,
        )

        try:
            return await acoustid.process()
        except Exception as e:
            self.logger.error(f"{self.name}: fingerprinting failed — {e}")
            raise
