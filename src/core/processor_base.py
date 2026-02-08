# src/core/processor_base.py
from __future__ import annotations
# import asyncio
from typing import Any, Dict, Optional, Sequence, ClassVar

from Singletons import Logger
from config import Config
from .enums import TaskType
# from .registry import registry
from .concurrency_mixin import ConcurrencyMixin


class ProcessorBase(ConcurrencyMixin):
    """
    Short-lived processor base. Instances are created per-run by ProcessorLoop.
    Inherits ConcurrencyMixin to allow the scheduler and TaskManager to enforce exclusivity/heavy_io.
    """

    # metadata (override in subclass)
    name: ClassVar[str] = None
    description: ClassVar[str] = None
    author: ClassVar[str] = None
    version: ClassVar[str] = None

    # scheduling hints
    exclusive: ClassVar[bool] = None
    heavy_io: ClassVar[bool] = None
    cooldown: ClassVar[float] = 3600.0
    max_heavy_io: ClassVar[int] = 2

    # DI
    depends: ClassVar[Sequence[str]] = None

    # optional progress
    supports_progress: ClassVar[bool] = None

    def __init__(self, **kwargs: Any) -> None:
        ConcurrencyMixin.__init__(self)  # initialize concurrency pieces
        self.config = Config.get_sync()
        self.logger = Logger()
        self._emitted_tasks: list[Dict[str, Any]] = []
        self._progress: float = 0.0
        self._completed: bool = False

        # ensure name exists
        if not self.name:
            self.name = self.__class__.__name__.lower()

    async def __call__(self) -> None:
        """
        Called by ProcessorLoop to execute one short-lived run.
        ProcessorLoop will call acquire_concurrency() before calling this instance.
        """
        try:
            await self.run()
            self.set_completed(f"{self.name}: completed")
        except Exception as e:
            self.logger.exception(f"{self.name}: error during run: {e}")
            self.set_completed(f"{self.name}: failed: {e}")

    # subclasses must implement
    async def run(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        """Optional stop hook for processor loop shutdown."""
        return None

    # progress API
    def set_progress(self, value: Optional[float] = None) -> None:
        if not self.supports_progress:
            return
        if value is None:
            self._progress = min(1.0, self._progress + 0.01)
        else:
            self._progress = max(0.0, min(1.0, float(value)))

    def set_completed(self, message: str = "") -> None:
        self._completed = True
        self._progress = 1.0
        self.logger.info(message)

    # emission API
    def emit_task(self, *, task_type: TaskType, batch: Optional[Any] = None, priority: int = 10, extra: Optional[dict] = None) -> None:
        self._emitted_tasks.append({"task_type": task_type, "batch": batch, "priority": priority, "extra": extra or {}})
        self.logger.debug(f"{self.name}: emitted task {task_type.name}")

    def collect_emitted_tasks(self) -> list[Dict[str, Any]]:
        return self._emitted_tasks
