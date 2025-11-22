from typing import Dict, Any, ClassVar
from pydantic import ValidationError

from ..core.audioutil_base import AudioUtilBase, register_audioutil
from ..models import MetadataModel
from ..singletons import Logger


@register_audioutil
class ValidateFingerprintMetadata(AudioUtilBase):
    """
    Validates raw dict-like metadata with Pydantic's MetadataModel.
    Falls back to an empty MetadataModel on validation failure.
    """

    # ---- PluginBase metadata ----
    name: ClassVar[str] = "validate_fingerprint_metadata"
    description: ClassVar[str] = "Pydantic validation wrapper for raw fingerprint metadata."
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = False     # trivial transform, can run concurrently
    heavy_io: ClassVar[bool] = False      # no disk/network I/O

    def __init__(self):
        self.logger = Logger

    # --------------------------------
    # Main async API
    # --------------------------------
    async def run(self, raw: Dict[str, Any]) -> MetadataModel:
        try:
            return MetadataModel(**raw)
        except ValidationError as e:
            self.logger.debug(
                f"ValidateFingerprintMetadata: validation failed, using empty model. Error: {e}"
            )
            return MetadataModel()
