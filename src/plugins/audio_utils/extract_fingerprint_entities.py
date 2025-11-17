from typing import Dict, Any

from ..core.decorators import register_audioutil
from ..core.audioutil_base import AudioUtilBase
from ..models import MetadataModel


@register_audioutil
class ExtractFingerprintEntities(AudioUtilBase):
    """
    Normalizes artists + track info for task consumption.
    """

    name = "extract_fp_entities"
    depends: list[str] = []

    async def run(self, metadata: MetadataModel) -> Dict[str, Any]:
        return {
            "artists": [
                {"name": a.name, "mbid": a.mbid}
                for a in metadata.artists
            ],
            "title": metadata.title,
            "mbid": metadata.mbid,
        }
