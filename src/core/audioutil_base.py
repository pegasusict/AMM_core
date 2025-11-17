# src/core/audioutil_base.py
from __future__ import annotations
from typing import Optional, ClassVar
import re

from ..Singletons import Logger, Config
from ..core.enums import PluginType

class AudioUtilBase:
    """Minimal base class for audio utility plugins."""

    # --- Static metadata ---
    plugin_type: ClassVar[PluginType] = PluginType.AUDIOUTIL
    name: ClassVar[str]
    description: ClassVar[str]
    depends: ClassVar[list[str]]
    version: ClassVar[str]      # "0.0.0"


    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = Logger(self.config)

    @classmethod
    async def create_async(cls, *args, **kwargs):
        """Optional async factory hook. Override if needed."""
        return cls(*args, **kwargs)

    async def init(self):
        """Optional async initializer on instances."""
        return None

    @classmethod
    def _validate_classvars(cls):
        """Validates all ClassVar fields."""
        name_filter = re.compile("^[a-zA-Z][a-zA-Z0-9_]*$")
        description_filter = re.compile("^[a-zA-Z ][a-zA-Z0-9_ .,!?]*$")
        version_filter = re.compile("^[0-9]+\.[0-9]+\.[0-9]+$")


        if cls.plugin_type != PluginType.AUDIOUTIL:
            raise ValueError("plugin_type must be PluginType.AUDIOUTIL")

        if not cls.name:
            raise ValueError("name must be set")
        if not name_filter.match(cls.name):
            raise ValueError("name must be a valid Python identifier")

        if not cls.description:
            raise ValueError("description must be set")
        if not description_filter.match(cls.description):
            raise ValueError("description must be a valid string")

        if isinstance(cls.depends, list):
            raise ValueError("depends must be set")
        if cls.depends.len() > 0:
            raise ValueError("depends must be an empty list")

        if not cls.version:
            raise ValueError("version must be set")
        if not version_filter.match(cls.version):
            raise ValueError("version must be a valid semver string")
