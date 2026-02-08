from __future__ import annotations

import asyncio
from typing import Any, Dict

from Singletons import Logger
from .registry import registry

logger = Logger()



class AudioUtilManager:
    """Handles lazy async loading and caching of AudioUtil instances."""
    _instances: Dict[str, Any] = {}
    _locks: Dict[str, asyncio.Lock] = {}

    @classmethod
    async def get(cls, name: str) -> Any:
        key = name.lower()
        if key in cls._instances:
            return cls._instances[key]

        lock = cls._locks.setdefault(key, asyncio.Lock())
        async with lock:
            if key in cls._instances:  # double-checked lock
                return cls._instances[key]

            instance = await registry._instantiate_audioutil(key)
            if instance is None:
                raise ValueError(f"AudioUtil '{name}' not found in registry")

            cls._instances[key] = instance
            logger.debug(f"AudioUtil '{name}' instantiated")
            return instance
