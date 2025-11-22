# watcher.py

# import asyncio
from watchfiles import awatch
import logging
from pathlib import Path

logger = logging.getLogger("AMM.ConfigWatcher")


async def watch_file(path: Path, callback):
    """
    Watches config file and calls the callback on change.
    """
    async for _ in awatch(path):
        logger.info("Detected config change, reloading...")
        try:
            await callback()
        except Exception as e:
            logger.error(f"Error applying reload: {e}")
