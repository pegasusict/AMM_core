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
import multiprocessing
from pathlib import Path
from typing import Any, List, Callable, Optional

from ..Exceptions import InvalidValueError

from ..models import TaskType, TaskStatus
from ..Singletons.config import Config


class Task:
    """Task Parent class to be used by tasks which are managed by TaskManager."""

    processed: int = 0
    process: multiprocessing.Process
    connfig: Config | None = None

    @property
    def batch(self) -> dict[str, str] | dict[int, str] | List[str | Path] | List[Path]:
        """Returns the batch of items to be processed by the task."""
        return self.batch

    @batch.setter
    def batch(
        self, value: dict[str, str] | dict[int, str] | List[str | Path] | List[Path]
    ) -> None:
        """Sets the batch of items to be processed by the task."""
        if not isinstance(value, (dict, list)):
            raise ValueError("Batch must be a dictionary or a list")
        self.batch = value

    @property
    def task_status(self) -> TaskStatus:
        """Returns the status of the task."""
        return self.task_status

    @task_status.setter
    def task_status(self, value: TaskStatus) -> None:
        """Sets the status of the task."""
        if not isinstance(value, TaskStatus):
            raise ValueError("task_status must be a TaskStatus enum")
        self.task_status = value

    @property
    def task_type(self) -> TaskType:
        """Returns the type of the task."""
        return self.task_type

    @task_type.setter
    def task_type(self, value: TaskType) -> None:
        """Sets the type of the task."""
        if not isinstance(value, TaskType):
            raise ValueError("task_type must be a TaskType enum")
        self.task_type = value

    @property
    def task_id(self) -> str:
        """Returns the ID of the task."""
        return self.task_id

    @task_id.setter
    def task_id(self, value: str) -> None:
        """Sets the ID of the task."""
        if not isinstance(value, str):
            raise ValueError("task_id must be a string")
        self.task_id = value

    @property
    def start_time(self) -> float:
        """Returns the start time of the task."""
        return self.start_time

    @start_time.setter
    def start_time(self, value: float | int) -> None:
        """Sets the start time of the task."""
        if not isinstance(value, (float, int)):
            raise ValueError("start_time must be a float or int")
        self.start_time = value

    @property
    def end_time(self) -> float:
        """Returns the end time of the task."""
        return self.end_time

    @end_time.setter
    def end_time(self, value: float | int) -> None:
        """Sets the end time of the task."""
        if not isinstance(value, (float, int)):
            raise ValueError("end_time must be a float or int")
        self.end_time = value

    @property
    def duration(self) -> float:
        """Returns the duration of the task."""
        return self.duration

    @duration.setter
    def duration(self, value: float | int) -> None:
        """Sets the duration of the task."""
        if not isinstance(value, (float, int)):
            raise ValueError("duration must be a float or int")
        self.duration = value

    @property
    def progress(self) -> float:
        """Returns the progress of the task."""
        return self.progress

    @progress.setter
    def progress(self, value: float | int) -> None:
        """Sets the progress of the task."""
        if not isinstance(value, (float, int)):
            raise ValueError("progress must be a float or int")
        self.progress = value

    @property
    def result(self) -> str | bool:
        """Returns the result of the task."""
        return self.result

    @result.setter
    def result(self, value: str | bool) -> None:
        """Sets the result of the task."""
        if not isinstance(value, (str, bool)):
            raise ValueError("result must be a string or boolean")
        self.result = value

    @property
    def error(self) -> str:
        """Returns the error message of the task."""
        return self.error

    @error.setter
    def error(self, value: str) -> None:
        """Sets the error message of the task."""
        if not isinstance(value, str):
            raise ValueError("error must be a string")
        self.error = value

    @property
    def status(self) -> TaskStatus:
        """Returns the current status of the task."""
        return self.status

    @status.setter
    def status(self, value: TaskStatus) -> None:
        """Sets the current status of the task."""
        if not isinstance(value, TaskStatus):
            raise ValueError("status must be a TaskStatus enum")
        self.status = value

    @property
    def old_status(self) -> TaskStatus:
        """Returns the previous status of the task."""
        return self.old_status

    @old_status.setter
    def old_status(self, value: TaskStatus) -> None:
        """Sets the previous status of the task."""
        if not isinstance(value, TaskStatus):
            raise ValueError("old_status must be a TaskStatus enum")
        self.old_status = value

    @property
    def target(self) -> Callable | None:
        """Returns the target function to be executed by the task."""
        return self.target

    @target.setter
    def target(self, value: Callable | None) -> None:
        """Sets the target function to be executed by the task."""
        if value is not None and not callable(value):
            raise ValueError("target must be a callable function")
        self.target = value

    def run(self) -> None:
        """Runs the task."""
        raise NotImplementedError("Subclasses must implement this method")

    def start(self) -> None:
        """Starts the task."""
        self.start_time = time.time()
        self.set_status(TaskStatus.RUNNING)
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()

    def __init__(self, config: Config, task_type: TaskType):
        """Initializes the Task class."""
        self.config = config
        self.task_type = task_type
        self.task_status = TaskStatus.PENDING
        self.process: multiprocessing.Process = multiprocessing.Process(
            target=self._wrapper
        )
        self.set_id()

    def _wrapper(self) -> None:
        """Wrapper method to run the task."""
        if self.target:
            self.target(self.batch)
        else:
            raise NotImplementedError("Subclasses must implement the target method")

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
                if not self.error:
                    self.error = "Task failed with exit code {}".format(
                        self.process.exitcode
                    )
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
            self.result = False
            self.error = "Task cancelled"
            self.process = None  # type: ignore
            TaskManager().unregister_task(self.task_id, self.task_status)
            return True
        return False

    def get_progress(self):
        """
        Returns the progress of the task.
        """
        return self.progress

    def get_result(self) -> str | bool:
        """
        Returns the result of the task.
        """
        return self.result or False

    def set_result(self, result: str | None) -> None:
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
            self.process = None  # type: ignore

    def get_error(self) -> str:
        """
        Returns the error of the task.
        """
        return self.error

    def set_error(self, error: str) -> None:
        """
        Sets the error of the task.
        """
        self.error = error
        self.set_status(TaskStatus.FAILED)
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.progress = 100
        self.process = None  # type: ignore

    def get_id(self) -> str:
        """Returns the task ID."""
        return self.task_id

    def set_id(self) -> None:
        """Sets the task ID."""
        if not hasattr(self, "task_id") or self.task_id is None or self.task_id == "":
            if not hasattr(self, "task_type") or self.task_type is None:
                raise InvalidValueError("task_type must be set before setting task_id")
            task_name = self.task_type.value
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            self.task_id = f"{task_name}_{timestamp}"

    def get_status(self):
        """Returns the status of the task."""
        return self.task_status

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
            self.process = None  # type: ignore
        TaskManager().update_task_status(self)

    def get_old_status(self) -> TaskStatus:
        """Gets the old status of the Task."""
        return self.old_status

    def get_type(self) -> str:
        """Returns the task type."""
        return self.task_type.value

    def set_type(self, task_type: TaskType) -> None:
        """Sets the task type."""
        if task_type not in TaskType:
            raise ValueError(f"{task_type} is not a valid TaskType")
        self.task_type = task_type

    def set_finished(self) -> None:
        """Sets the task end time, duration, and progress to 100%.
        Unsets Process and sets the task status to COMPLETED."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.progress = 100
        self.process = None  # type: ignore
        self.task_status = TaskStatus.COMPLETED

    def set_progress(self) -> None:
        """This method increments the processed count and calculates the progress percentage."""
        self.processed += 1
        self.progress = (self.processed / len(self.batch)) * 100

    def is_alive(self) -> bool:
        return self.process.is_alive()

    def join(self) -> None:
        self.process.join()


class TaskManager:
    """TaskManager."""

    # class singleton instance
    _instance = None

    # dictionary to hold tasks by their status
    # dict[status: str, dict[task_id: str, Task]]
    tasks: dict[str, dict[str, Task]] = {}

    def __new__(cls):
        if not hasattr(cls, "instance") or cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.tasks = {}
        return cls._instance

    @classmethod
    def register_task(cls, task: Task) -> None:
        """Registers a Task in de TaskManager."""
        status = str(task.get_status())
        if status not in cls.tasks:
            cls.tasks[status] = {}
        cls.tasks[status][task.get_id()] = task  # type: ignore

    def update_task_status(self, task: Task) -> None:
        """Updates de listing of a Task whose status has been changed."""
        self.unregister_task(task.get_id(), task.get_old_status())
        self.register_task(task)

    def unregister_task(self, task_id: str, status: TaskStatus) -> None:
        """Unregisters a Task."""
        if status.value in self.tasks and task_id in self.tasks[status.value]:
            del self.tasks[status.value][task_id]

    def start_task(
        self,
        target: Callable,
        batch: dict[str, str] | dict[int, str] | List[str | Path] | List[Path],
        kwargs: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        The `start_task` function creates and starts a new task with the specified target function,
        arguments, and keyword arguments.

        :param target: The `target` parameter in the `start_task` method is expected to be a callable object
        (function, method, etc.) that represents the task to be executed. When `start_task` is called, it
        will create a `Task` object with the provided `target`, `args`, and
        :type target: Callable
        :param args: The `args` parameter in the `start_task` method is a tuple that contains the positional
        arguments to be passed to the `target` function when it is called. In this case, the default value
        for `args` is an empty tuple `()`, which means that if no arguments are provided
        :type args: Tuple
        :param kwargs: The `kwargs` parameter in the `start_task` method is a dictionary that allows you to
        pass keyword arguments to the target function `target`. These keyword arguments will be unpacked and
        passed to the target function when it is called
        :type kwargs: Optional[dict[str, Any]]
        :return: The `start_task` method returns the `id` of the task that was started.
        """
        task = target(
            config=Config(),
            batch=batch,
            kwargs=kwargs if kwargs is not None else {},
        )
        self.tasks[TaskStatus.RUNNING][task.task_id] = task
        task.start()
        print(f"Task {task.task_id} started.")
        return task.task_id

    def get_task(self, task_id: str) -> Task | bool:
        """Function to get a task by its ID.
        If the task is found, it returns the task object.
        If the task is not found, it returns False.

        Args:
            task_id (str): The ID of the task to be retrieved.
        :return: Task object or False if not found
        """
        if not task_id or not isinstance(task_id, str):
            raise InvalidValueError("task_id must be a non-empty string")
        task = False
        task_status = None
        # Iterate through all task statuses to find the task
        if not self.tasks:
            return False
        found = False
        for status in self.tasks:
            if task_id in self.tasks[status]:
                found = True
                task_status = status
                break
        if found:
            task = self.tasks[task_status].get(task_id) # type: ignore
        return task if task else False

    def stop_task(self, task_id: str) -> None:
        """Function to stop a task by its ID.
        This function checks if the task is alive and then cancels it.
        If the task is not found or already finished, it prints a message.

        Args:
            task_id (str): The ID of the task to be stopped.
        :return: None
        """
        if not task_id or not isinstance(task_id, str):
            raise InvalidValueError("task_id must be a non-empty string")

        task = self.get_task(task_id)
        if task and task.status == TaskStatus.RUNNING: # type: ignore
            # Check if the task is alive before attempting to cancel it
            if not hasattr(task, "is_alive") or not callable(task.is_alive): # type: ignore
                raise InvalidValueError("Task does not have an is_alive method")
            # Attempt to cancel the task
            if task and task.is_alive(): # type: ignore
                task.cancel() # type: ignore
                print(f"Task {task_id} terminated.")
            else:
                print(f"Task {task_id} not found or already finished.")
        else:
            print(f"Task {task_id} not found or already finished.")

    def task_status(self, task_id: str) -> Optional[dict[str, Any]]:
        task = self.get_task(task_id)
        if task:
            return {"id": task.id, "alive": task.is_alive(), "status": task.status()} # type: ignore
        return None

    def list_tasks(self) -> list[dict[str, str | bool]]:
        result: list[dict[str, str | bool]] = []

        for status, task_group in self.tasks.items():
            for task_id, task in task_group.items():
                result.append({
                    "task_id": task_id,
                    "status": status,
                    "alive": task.is_alive(),
                })

        return result
