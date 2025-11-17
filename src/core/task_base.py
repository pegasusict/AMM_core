# -*- coding: utf-8 -*-
#  Copyleft 2021-2025 Mattijs Snepvangers.
#  Part of Audiophiles' Music Manager (AMM)
#
#  Licensed under the GPL v3 or later.

from __future__ import annotations

import time
import datetime as dt
import re
from typing import Any, Optional, Callable, ClassVar
from abc import ABC, abstractmethod

from ..core.enums import PluginType, TaskStatus, StageType, TaskType


class TaskBase(ABC):
    """
    Unified async-compatible base class for all AMM tasks.

    Provides:
      - Lifecycle management (start, stop, cancel, progress)
      - Logging & configuration injection
      - Dependency declaration
      - Stage and plugin metadata
    """

    # --- Static metadata ---
    plugin_type: ClassVar[PluginType] = PluginType.TASK
    name: ClassVar[str]
    description: ClassVar[str]
    depends: ClassVar[list[str]]
    stage_type: ClassVar[StageType]
    task_type: ClassVar[TaskType]
    version: ClassVar[str]      # "0.0.0"

    # --- Instance attributes ---
    _status: TaskStatus
    _old_status: TaskStatus
    _start_time: float
    _end_time: float
    _duration: float
    _progress: float
    _result: str | bool
    _error: str
    _task_id: str

    batch: list[Any] | dict[Any, Any] | None
    config: Any
    logger: Any

    def __init__(
        self,
        *,
        config: Any,
        batch: Optional[list[Any] | dict[Any, Any]] = None,
        logger: Optional[Any] = None,
        **kwargs,
    ):
        self._validate_classvars()
        self.config = config
        self.logger = logger or getattr(config, "logger", None)
        self.batch = batch
        self.kwargs = kwargs

        self._status = TaskStatus.PENDING
        self._old_status = TaskStatus.PENDING
        self._start_time = 0.0
        self._end_time = 0.0
        self._duration = 0.0
        self._progress = 0.0
        self._result = False
        self._error = ""
        self._task_id = self._make_id()

        self.processed = 0
        self._target: Optional[Callable] = None

    @classmethod
    def _validate_classvars(cls):
        """Validates all ClassVar fields."""
        name_filter = re.compile("^[a-zA-Z][a-zA-Z0-9_]*$")
        description_filter = re.compile("^[a-zA-Z ][a-zA-Z0-9_ .,!?]*$")
        version_filter = re.compile("^[0-9]+\.[0-9]+\.[0-9]+$")


        if cls.plugin_type != PluginType.TASK:
            raise ValueError("plugin_type must be PluginType.TASK")

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

        if not cls.stage_type:
            raise ValueError("stage_type must be set")
        if type(cls.stage_type) is not StageType:
            raise ValueError("stage_type must be a StageType enum")

        if not cls.version:
            raise ValueError("version must be set")
        if not version_filter.match(cls.version):
            raise ValueError("version must be a valid semver string")

        if not cls.task_type:
            raise ValueError("task_type must be set")
        if type(cls.task_type) is not TaskType:
            raise ValueError("task_type must be a TaskType enum")

    # --- Core API ---

    @abstractmethod
    async def run(self, *args, **kwargs) -> None:
        """Main task execution logic."""

    # --- Status and lifecycle management ---

    def _make_id(self) -> str:
        timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
        return f"{self.name}_{timestamp}"

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def status(self) -> TaskStatus:
        return self._status

    @status.setter
    def status(self, value: TaskStatus):
        if not isinstance(value, TaskStatus):
            raise ValueError("Status must be a TaskStatus enum")
        self._old_status = self._status
        self._status = value

    @property
    def progress(self) -> float:
        return self._progress

    def set_progress(self, step: int | float = 1):
        self.processed += step
        total = len(self.batch) if self.batch else 0
        if total > 0:
            self._progress = (self.processed / total) * 100
        if self.logger:
            self.logger.debug(f"{self.name}: progress={self._progress:.2f}%")

    def set_start_time(self):
        self._start_time = time.time()
        self.status = TaskStatus.RUNNING

    def set_end_time_to_now(self):
        self._end_time = time.time()
        self._duration = self._end_time - self._start_time
        if self.status != TaskStatus.FAILED:
            self.status = TaskStatus.COMPLETED
        if self.logger:
            self.logger.debug(
                f"{self.name}: completed in {self._duration:.2f}s"
            )

    def set_error(self, message: str):
        self._error = message
        self.status = TaskStatus.FAILED
        self._end_time = time.time()
        self._duration = self._end_time - self._start_time
        self._progress = 100.0
        self._result = False
        if self.logger:
            self.logger.error(f"{self.name}: failed — {message}")

    async def start(self):
        """Entry point for async execution."""
        self.set_start_time()
        try:
            await self.run()
        except Exception as e:
            self.set_error(str(e))
        finally:
            self.set_end_time_to_now()

    def cancel(self):
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self._end_time = time.time()
        self._duration = self._end_time - self._start_time
        self._result = False
        self._error = "Task cancelled"
        if self.logger:
            self.logger.info(f"{self.name}: cancelled")

    # --- Convenience accessors ---
    @property
    def duration(self) -> float:
        return self._duration

    @property
    def result(self) -> str | bool:
        return self._result

    @property
    def error(self) -> str:
        return self._error
