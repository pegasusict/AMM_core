# -*- coding: utf-8 -*-
"""Base logic for plugin discovery and registration."""

from typing import Optional
from ..singletons import Logger
from .registry import audio_util_registry, processor_registry, task_registry, stage_registry
from .enums import StageType, PluginType

logger = Logger()


class PluginBase:
    """Base class for all AMM plugins."""

    # Each subclass must define:
    # - plugin_type: PluginType
    # - name: str
    # - stage: StageType
    # - stage_name: str
    plugin_type: PluginType = None
    name: str = "Unnamed"
    stage: Optional[StageType] = None
    stage_name: Optional[str] = None

    def __init_subclass__(cls, **kwargs):
        """Automatically registers plugin class when subclassed."""
        super().__init_subclass__(**kwargs)

        if not getattr(cls, "plugin_type", None):
            logger.warning(f"⚠️ Plugin '{cls.__name__}' missing plugin_type — skipped registration.")
            return

        if not getattr(cls, "name", None):
            cls.name = cls.__name__

        # --- Register in type-specific registry ---
        registry_map = {
            PluginType.AUDIOUTIL: audio_util_registry,
            PluginType.PROCESSOR: processor_registry,
            PluginType.TASK: task_registry,
        }

        registry = registry_map.get(cls.plugin_type)
        if not registry:
            logger.warning(f"⚠️ Unknown plugin_type '{cls.plugin_type}' for {cls.__name__}")
            return

        registry.register(cls.name, cls)
        logger.debug(f"🔌 Registered plugin: {cls.plugin_type} → {cls.name}")

        if cls.stage and cls.stage_name:
            stage_registry.register_stage(cls.stage_name, cls.stage, cls.name)

