import asyncio

from registry import audio_util_registry
from singletons import Logger

logger = Logger()



class AudioUtilManager:
    """Handles lazy async loading and caching of AudioUtil instances."""
    _instances = {}
    _locks = {}

    @classmethod
    async def get(cls, name: str):
        if name in cls._instances:
            return cls._instances[name]

        if name not in cls._locks:
            cls._locks[name] = asyncio.Lock()

        async with cls._locks[name]:
            if name in cls._instances:  # double-checked lock
                return cls._instances[name]

            util_cls = audio_util_registry.get(name)
            if util_cls is None:
                raise ValueError(f"AudioUtil '{name}' not found in registry")

            instance = (
                await util_cls.create_async()
                if hasattr(util_cls, "create_async")
                else util_cls()
            )

            cls._instances[name] = instance
            logger.debug(f"AudioUtil '{name}' instantiated")
            return instance
