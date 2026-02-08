from dataclasses import dataclass
from typing import Optional

from .enums import StageType

@dataclass(frozen=True)
class Stage:
    name: str
    stage_type: StageType
    task: Optional[str] = None
    description: Optional[str] = None
    # additional metadata can be added later (timeout, retries, etc.)

    @property
    def type(self) -> StageType:
        # Compatibility alias for older call sites.
        return self.stage_type
