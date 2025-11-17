from typing import Dict, Any
from pydantic import ValidationError

from ..core.decorators import register_audioutil
from ..core.audioutil_base import AudioUtilBase
from ..models import MetadataModel


@register_audioutil
class ValidateFingerprintMetadata(AudioUtilBase):
    """
    Pydantic validation wrapper for metadata.
    """

    name = "validate_fingerprint_metadata"
    depends: list[str] = []

    async def run(self, raw: Dict[str, Any]) -> MetadataModel:
        try:
            return MetadataModel(**raw)
        except ValidationError:
            return MetadataModel()
