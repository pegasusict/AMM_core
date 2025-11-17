# src/core/processor_base.py
from __future__ import annotations
from typing import Optional, Any, ClassVar
from abc import ABC
import re

from ..core.enums import PluginType, TaskType
from ..Singletons import Logger, Config

class ProcessorBase(ABC):
    # --- Static metadata ---
    plugin_type: ClassVar[PluginType] = PluginType.PROCESSOR
    name: ClassVar[str]
    description: ClassVar[str]
    depends: ClassVar[list[str]]
    task_type: ClassVar[TaskType]
    version: ClassVar[str]

    def __init__(self, *audioutils: Any, config: Optional[Config] = None, **kwargs):
        self._validate_classvars()
        self.config = config or Config()
        self.logger = Logger(self.config)
        self._audioutils = list(audioutils)
        self.kwargs = kwargs

    @classmethod
    def _validate_classvars(cls):
        """Validates all ClassVar fields."""
        name_filter = re.compile("^[a-zA-Z][a-zA-Z0-9_]*$")
        description_filter = re.compile("^[a-zA-Z ][a-zA-Z0-9_ .,!?]*$")
        version_filter = re.compile("^[0-9]+\.[0-9]+\.[0-9]+$")


        if cls.plugin_type != PluginType.PROCESSOR:
            raise ValueError("plugin_type must be PluginType.PROCESSOR")

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
        for item in cls.depends:
            if not isinstance(item, str):
                raise ValueError("depends must be a list of strings")
            if not name_filter.match(item):
                raise ValueError("depends items must be valid Python identifiers")

        if not cls.version:
            raise ValueError("version must be set")
        if not version_filter.match(cls.version):
            raise ValueError("version must be a valid semver string")

        if not cls.task_type:
            raise ValueError("task_type must be set")
        if type(cls.task_type) is not TaskType:
            raise ValueError("task_type must be a TaskType enum")
