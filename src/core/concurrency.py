# src/core/concurrency.py
from __future__ import annotations

import asyncio

# System-wide exclusive lock shared across processors/tasks
system_exclusive_lock: asyncio.Lock = asyncio.Lock()


async def acquire_exclusive() -> None:
    await system_exclusive_lock.acquire()


def release_exclusive() -> None:
    if system_exclusive_lock.locked():
        system_exclusive_lock.release()
