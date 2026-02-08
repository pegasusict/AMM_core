# src/core/concurrency_mixin.py
from __future__ import annotations

import asyncio
import time
from typing import ClassVar, Optional

from Singletons import Logger
from .concurrency import system_exclusive_lock


class ConcurrencyMixin:
    """
    Shared concurrency control for Processors and Tasks.
    - exclusive: global exclusive lock (one holder at a time)
    - heavy_io: semaphore pool for heavy IO work
    - cooldown: per-instance cooldown after completion
    """

    # Shared primitives (module/class-level)
    _exclusive_lock: asyncio.Lock = system_exclusive_lock
    _heavy_io_semaphore: Optional[asyncio.Semaphore] = None
    _heavy_io_max: int = 2  # default; can be overridden

    # defaults (instances / subclasses override)
    exclusive: ClassVar[Optional[bool]] = None
    heavy_io: ClassVar[Optional[bool]] = None
    cooldown: float = 3600.0
    max_heavy_io: int = 2

    def __init__(self) -> None:
        self.logger = Logger()
        self._cooldown_until: float = 0.0

        # lazily create the heavy io semaphore once (respecting configured max)
        if ConcurrencyMixin._heavy_io_semaphore is None:
            ConcurrencyMixin._heavy_io_max = getattr(self, "max_heavy_io", ConcurrencyMixin._heavy_io_max)
            ConcurrencyMixin._heavy_io_semaphore = asyncio.Semaphore(ConcurrencyMixin._heavy_io_max)

    # ---------------- cooldown ----------------
    def is_in_cooldown(self) -> bool:
        return time.time() < self._cooldown_until

    def start_cooldown(self) -> None:
        if getattr(self, "cooldown", 0.0) > 0:
            self._cooldown_until = time.time() + float(self.cooldown)

    # ----------- acquisition / release API -----------
    async def acquire_concurrency(self) -> bool:
        """
        Acquire required concurrency primitives.
        Returns True if caller may run, False if not (e.g. cooldown or cannot acquire).
        Caller MUST call release_concurrency() after completion if True was returned.
        """
        # cooldown check
        if self.is_in_cooldown():
            self.logger.debug(f"{getattr(self, 'name', type(self).__name__)}: in cooldown until {self._cooldown_until}")
            return False

        # exclusive takes global lock
        if getattr(self, "exclusive", False):
            # block until acquired — this is the design: exclusive must wait
            try:
                await ConcurrencyMixin._exclusive_lock.acquire()
                self.logger.debug(f"{getattr(self, 'name', type(self).__name__)}: acquired exclusive lock")
                return True
            except Exception as e:
                self.logger.exception(f"acquire_concurrency (exclusive) error: {e}")
                return False

        # heavy_io tries to acquire a semaphore slot (blockable)
        if getattr(self, "heavy_io", False):
            sem = ConcurrencyMixin._heavy_io_semaphore
            if sem is None:
                # initialize fallback (should not happen)
                ConcurrencyMixin._heavy_io_semaphore = asyncio.Semaphore(getattr(self, "max_heavy_io", 2))
                sem = ConcurrencyMixin._heavy_io_semaphore

            try:
                await sem.acquire()
                self.logger.debug(f"{getattr(self, 'name', type(self).__name__)}: acquired heavy_io slot")
                return True
            except Exception as e:
                self.logger.exception(f"acquire_concurrency (heavy_io) error: {e}")
                return False

        # no special constraints
        return True

    def release_concurrency(self) -> None:
        """
        Release any previously acquired concurrency primitives and start cooldown.
        Safe to call even if nothing was acquired.
        """
        # start cooldown always
        self.start_cooldown()

        # release exclusive lock if held
        try:
            if getattr(self, "exclusive", False) and ConcurrencyMixin._exclusive_lock.locked():
                ConcurrencyMixin._exclusive_lock.release()
                self.logger.debug(f"{getattr(self, 'name', type(self).__name__)}: released exclusive lock")
        except RuntimeError:
            # already released or not owned by this loop
            pass

        # release heavy_io semaphore if used
        try:
            if getattr(self, "heavy_io", False) and ConcurrencyMixin._heavy_io_semaphore is not None:
                ConcurrencyMixin._heavy_io_semaphore.release()
                self.logger.debug(f"{getattr(self, 'name', type(self).__name__)}: released heavy_io slot")
        except ValueError:
            # semaphore release mismatch — ignore
            pass
