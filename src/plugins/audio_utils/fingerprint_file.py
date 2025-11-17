from pathlib import Path
from typing import Dict, Any

from ..core.decorators import register_audioutil
from ..core.audioutil_base import AudioUtilBase
from ..core.exceptions import FileError
from ..AudioUtils import Tagger, get_file_type, MediaParser, AcoustID
from ..AudioUtils.utils.acoustidhttpclient import AcoustIDHttpClient


@register_audioutil
class FingerprintFile(AudioUtilBase):
    """
    Performs AcoustID fingerprinting and returns raw metadata.
    """

    name = "fingerprint_file"
    depends: list[str] = []

    async def run(self, path: Path) -> Dict[str, Any]:
        file_type = get_file_type(path)
        if file_type is None:
            raise FileError(f"FingerPrinter: Illegal filetype: {path}")

        acoustid = AcoustID(
            path=path,
            acoustid_client=AcoustIDHttpClient(),
            tagger=Tagger(path, file_type),
            parser=MediaParser(),
            logger=None,  # logging handled by the task
        )
        return await acoustid.process()
