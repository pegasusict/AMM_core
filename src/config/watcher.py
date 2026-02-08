# watcher.py

from __future__ import annotations

from typing import Awaitable, Callable
import logging
from pathlib import Path

from watchfiles import awatch

logger = logging.getLogger("AMM.ConfigWatcher")


async def watch_file(path: Path, callback: Callable[[], Awaitable[None]]) -> None:
    """
    Watches config file and calls the callback on change.
    """
    async for _ in awatch(path):
        logger.info("Detected config change, reloading...")
        try:
            await callback()
        except Exception as e:
            logger.error(f"Error applying reload: {e}")
