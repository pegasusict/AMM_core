# src/core/processor_base.py
from __future__ import annotations
from typing import Any, ClassVar
from abc import ABC

from .enums import PluginType, TaskType
from .registry import registry

class ProcessorBase(ABC):
    # --- Static metadata ---
    plugin_type: ClassVar[PluginType] = PluginType.PROCESSOR
    name: ClassVar[str]
    description: ClassVar[str]
    author: ClassVar[str]
    depends: ClassVar[tuple[str, ...]] = ()
    task_type: ClassVar[TaskType]
    version: ClassVar[str]
    exclusive: ClassVar[bool] = None
    heavy_io: ClassVar[bool] = None


    def __init__(self, *audioutils: Any, **kwargs):
        self._audioutils = list(audioutils)
        self.kwargs = kwargs

def register_processor(cls):
    cls._validate_classvars()
    if getattr(cls, "plugin_type", None) != PluginType.PROCESSOR:
        raise TypeError("Processor class must set plugin_type == PluginType.PROCESSOR")
    registry.register_processor(cls)
    return cls
