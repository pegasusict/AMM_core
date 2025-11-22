from __future__ import annotations
from abc import ABCMeta
from typing import ClassVar
import asyncio

from ..Singletons import Logger, Config
from .enums import PluginType
from .plugin_base import PluginBase
from .registry import registry



class AudioUtilBase(PluginBase, metaclass=ABCMeta):
    """Minimal base class for audio utility plugins."""

    # --- Static metadata ---
    plugin_type: ClassVar[PluginType] = PluginType.AUDIOUTIL
    name: ClassVar[str]
    description: ClassVar[str]
    version: ClassVar[str]
    author: ClassVar[str]

    def __init__(self):
        self.config = Config()
        self.logger = Logger(self.config)

    # lifecycle hooks
    @classmethod
    async def create_async(cls, *args, **kwargs) -> "AudioUtilBase":
        """
        Optional factory create_async returning an initialized instance.
        Default falls back to __init__ + init().
        """
        inst = cls(*args, **kwargs)
        init_fn = getattr(inst, "init", None)
        if init_fn and asyncio.iscoroutinefunction(init_fn):
            await init_fn()
        return inst

    async def init(self) -> None:
        """Optional instance-level async init; default no-op."""
        return None

def register_audioutil(cls):
    # validate class vars early
    cls._validate_classvars()
    # also ensure plugin_type is AUDIOUTIL
    if getattr(cls, "plugin_type", None) != PluginType.AUDIOUTIL:
        raise TypeError("AudioUtil class must set plugin_type == PluginType.AUDIOUTIL")
    registry.register_audioutil(cls)
    return cls
