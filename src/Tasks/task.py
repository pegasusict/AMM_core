# -*- coding: utf-8 -*-
#  Copyleft 2021-2025 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  AMM is free software: you can redistribute it and/or modify  it under the terms of the
#   GNU General Public License as published by  the Free Software Foundation, either version 3
#   of the License or any later version.
#
#  AMM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with AMM.  If not, see <https://www.gnu.org/licenses/>.

"""Task class for managing tasks in the application.
This module defines the Task class and its subclasses for different types of tasks.
It also defines the TaskType and TaskStatus enums for task management."""

import time
import datetime as dt
import multiprocessing as mproc
from pathlib import Path
from typing import Callable, Optional

from models import Codec

from ..Singletons.logger import Logger
from ..Enums import TaskType, TaskStatus, ArtType
from ..Singletons.config import Config


class Task:
    """Base class for asynchronous tasks managed by TaskManager."""

    batch: (
        list[str]
        | list[int]
        | list[Path]
        | dict[str, ArtType]
        | dict[int, Codec]
        | None
    ) = None

    def __init__(
        self,
        *,
        config: Config,
        task_type: TaskType = TaskType.CUSTOM,
        batch: list[str]
        | list[int]
        | list[Path]
        | dict[str, ArtType]
        | dict[int, Codec]
        | None = None,
        **kwargs,
    ):
        self.config = config
        self.logger = Logger(config)
        self._task_type = task_type
        self._status = TaskStatus.PENDING
        self._old_status = TaskStatus.PENDING

        self._task_id: str = ""
        self._start_time: float = 0.0
        self._end_time: float = 0.0
        self._duration: float = 0.0
        self._progress: float = 0.0
        self._result: str | bool = False
        self._error: str = ""

        self._target: Optional[Callable] = None
        self.batch = batch
        self.kwargs = kwargs
        self.processed: int = 0
        self.process: Optional[mproc.Process] = None

        self.set_id()

    # ----- Properties -----

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def task_type(self) -> TaskType:
        return self._task_type

    @property
    def status(self) -> TaskStatus:
        return self._status

    @status.setter
    def status(self, value: TaskStatus):
        if not isinstance(value, TaskStatus):
            raise ValueError("status must be a TaskStatus enum")
        self._old_status = self._status
        self._status = value

    @property
    def old_status(self) -> TaskStatus:
        return self._old_status

    @property
    def start_time(self) -> float:
        return self._start_time

    @start_time.setter
    def start_time(self, value: float | None):
        if value is None:
            value = time.time()
        elif not isinstance(value, (int, float)):
            raise ValueError("start_time must be a float or None")
        else:
            if value < 0:
                raise ValueError("start_time cannot be negative")
        self._start_time = float(value)

    @property
    def end_time(self) -> float:
        return self._end_time

    @end_time.setter
    def end_time(self, value: float | None):
        if value is None:
            value = time.time()
        elif not isinstance(value, (int, float)):
            raise ValueError("end_time must be a float or None")
        else:
            if value < 0:
                raise ValueError("end_time cannot be negative")
        self._end_time = float(value)

    @property
    def duration(self) -> float:
        return self._duration

    @duration.setter
    def duration(self, value: float | None):
        if value is None:
            value = self._end_time - self._start_time
        self._duration = float(value)

    @property
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, value: float):
        self._progress = float(value)

    @property
    def result(self) -> str | bool:
        return self._result

    @result.setter
    def result(self, value: str | bool):
        if not isinstance(value, (str, bool)):
            raise ValueError("result must be a string or boolean")
        self._result = value

    @property
    def error(self) -> str:
        return self._error

    @error.setter
    def error(self, value: str):
        if not isinstance(value, str):
            raise ValueError("error must be a string")
        self._error = value

    @property
    def target(self) -> Optional[Callable]:
        return self._target

    @target.setter
    def target(self, value: Optional[Callable]):
        if value is not None and not callable(value):
            raise ValueError("target must be a callable or None")
        self._target = value

    # ----- Core Methods -----

    def set_id(self):
        if not self._task_id:
            timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
            self._task_id = f"{self._task_type.value}_{timestamp}"

    def run(self):
        """Override this in subclasses."""
        raise NotImplementedError("Subclasses must implement `run()`.")

    def _wrapper(self):
        """Default execution wrapper used by multiprocessing."""
        try:
            if self._target:
                self._target(self.batch)
            else:
                self.run()
        except Exception as e:
            self.set_error(str(e))

    def start(self):
        self._start_time = time.time()
        self.status = TaskStatus.RUNNING
        self.process = mproc.Process(target=self._wrapper)
        self.process.start()

    def wait(self):
        if self.process and self.process.is_alive():
            self.process.join()
        self._end_time = time.time()
        self._duration = self._end_time - self._start_time
        if self.process and self.process.exitcode == 0:
            self.status = TaskStatus.COMPLETED
        else:
            self.set_error("Task failed")

    def pause(self):
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.status = TaskStatus.PAUSED
            self._end_time = time.time()
            self._duration = self._end_time - self._start_time
            self._result = "Paused"
            self.process = None

    def cancel(self):
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.status = TaskStatus.CANCELLED
            self._end_time = time.time()
            self._duration = self._end_time - self._start_time
            self._result = False
            self._error = "Task cancelled"
            self.process = None

    def set_error(self, message: str):
        self._error = message
        self.status = TaskStatus.FAILED
        self._end_time = time.time()
        self._duration = self._end_time - self._start_time
        self._progress = 100.0
        self._result = False
        self.process = None

    def set_progress(self):
        self.processed += 1
        if self.batch:
            total = len(self.batch)
        else:
            total = 0
        if total > 0:
            self._progress = (self.processed / total) * 100

    def is_alive(self) -> bool:
        return self.process.is_alive() if self.process else False

    def join(self):
        if self.process:
            self.process.join()
