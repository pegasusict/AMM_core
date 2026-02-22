from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Callable


class SlidingWindowRateLimiter:
    """Simple in-memory sliding-window limiter."""

    def __init__(self, *, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self._events: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str, *, max_attempts: int, window_seconds: int) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""
        if max_attempts <= 0 or window_seconds <= 0:
            return True, 0

        now = self._clock()
        cutoff = now - float(window_seconds)

        async with self._lock:
            queue = self._events.setdefault(key, deque())
            while queue and queue[0] <= cutoff:
                queue.popleft()

            if len(queue) >= max_attempts:
                retry_after = max(1, int(window_seconds - (now - queue[0])))
                return False, retry_after

            queue.append(now)
            return True, 0

    async def clear(self) -> None:
        async with self._lock:
            self._events.clear()


auth_rate_limiter = SlidingWindowRateLimiter()

