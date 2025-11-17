from dataclasses import dataclass
from typing import Optional

from .enums import StageType

@dataclass(frozen=True)
class Stage:
    name: str
    task: Optional[str] = None
    type: StageType
    description: Optional[str] = None
    # additional metadata can be added later (timeout, retries, etc.)
