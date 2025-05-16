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
import datetime
from multiprocessing import Process
from pathlib import Path

from ..models import TaskType, TaskStatus
from ..Singletons.config import Config

class Task():
    """Task Parent class to be used by tasks which are managed by TaskManager."""
    processed:int = 0
    batch:dict[str, str]|list[str]|list[Path]
    process:Process|None
    task_id:str
    result:str|None
    error:str
    start_time:float
    end_time:float
    duration: float
    progress: float = 0
    status:TaskStatus = TaskStatus.PENDING
    task_type:TaskType

    def __init__(self, config:Config, task_type:TaskType):
        """Initializes the Task class."""
        self.config = config
        self.task_type = task_type
        self.task_status = TaskStatus.PENDING

        task_name = task_type.value
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.task_id = f"{task_name}_{timestamp}"

        TaskManager().register_task(self) # type: ignore

    def run(self) -> None:
        """Runs the task."""
        raise NotImplementedError("Subclasses must implement this method")

    def start(self) -> None:
        """Starts the task."""
        self.start_time = time.time()
        self.set_status(TaskStatus.RUNNING)
        self.process = Process(target=self.run)
        self.process.start()

    def wait(self) -> bool:
        """
        Waits for the task to complete.
        """
        if self.process and self.process.is_alive():
            self.process.join()
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
            if self.process.exitcode == 0:
                self.set_status(TaskStatus.COMPLETED)
            else:
                self.set_status(TaskStatus.FAILED)
                self.error = "Task failed"
        return True

    def cancel(self) -> bool:
        """
        Cancels the task.
        """
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.set_status(TaskStatus.CANCELLED)
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
            self.progress = 100
            self.result = None
            self.error = "Task cancelled"
            self.process = None
            return True
        return False

    def get_status(self):
        """
        Returns the status of the task.
        """
        return self.task_status

    def get_progress(self):
        """
        Returns the progress of the task.
        """
        return self.progress

    def get_result(self) -> str|bool:
        """
        Returns the result of the task.
        """
        return self.result or False

    def set_result(self, result:str|None) -> None:
        """
        Sets the result of the task.
        """
        if result is not None:
            self.result = result
            self.set_status(TaskStatus.COMPLETED)
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
        else:
            self.set_status(TaskStatus.FAILED)
            self.error = "Task failed"
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
            self.progress = 100
            self.process = None

    def get_error(self) -> str:
        """
        Returns the error of the task.
        """
        return self.error

    def set_error(self, error:str) -> None:
        """
        Sets the error of the task.
        """
        self.error = error
        self.set_status(TaskStatus.FAILED)
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.progress = 100
        self.process = None

    def get_id(self) -> str:
        """
        Returns the task ID.
        """
        return self.task_id

    def set_status(self, task_status: TaskStatus) -> None:
        """Sets the task status."""
        self.old_status = self.status
        self.status = task_status
        if task_status == TaskStatus.COMPLETED:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
        elif task_status == TaskStatus.FAILED:
            self.error = "Task failed"
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
            self.progress = 100
            self.process = None
        TaskManager().update_task_status(self)

    def get_old_status(self) -> TaskStatus:
        """Gets the old status of the Task."""
        return self.old_status

    def get_type(self) -> str:
        """
        Returns the task type.
        """
        return self.task_type.value

    def set_type(self, task_type: TaskType) -> None:
        """
        Sets the task type.
        """
        if task_type not in TaskType:
            raise ValueError("task_type a valid TaskType")
        self.task_type = task_type

    def set_process(self, process: Process|None) -> None:
        """
        Sets the task process.
        """
        self.process = process

    def set_finished(self) -> None:
        """
        Sets the task end time, duration, and progress to 100%.
        Unstes Process and sets the task status to COMPLETED.
        """
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.progress = 100
        self.process = None
        self.task_status = TaskStatus.COMPLETED

    def set_progress(self) -> None:
        """
        Sets the progress of the task.

        Args:
            progress: The progress of the task.
        """
        self.processed += 1
        self.progress = (self.processed / len(self.batch)) * 100

class TaskManager:
    """TaskManager."""

    # class singleton instance
    instance = None

    tasks:dict[str, list[str]]

    def __new__(cls):
        if not hasattr(cls, 'instance') or cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.instance.tasks = {}
        return cls.instance

    @classmethod
    def register_task(cls, task:Task) -> None:
        """Registers a Task in de TaskManager."""
        status = str(task.get_status())
        if status not in cls.tasks:
            cls.tasks[status] = []
        cls.tasks[status][task.get_id()] = task # type: ignore

    def update_task_status(self, task:Task) -> None:
        """Updates de listing of a Task whose status has been changed."""
        self.unregister_task(task.get_id(), task.get_old_status())
        self.register_task(task)

    def unregister_task(self, task_id:str, status:TaskStatus) -> None:
        """Unregisters a Task."""
        status_str = str(status)
        if status_str in self.tasks and task_id in self.tasks[status_str]:
            self.tasks[status_str].remove(task_id)


