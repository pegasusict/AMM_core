# -*- coding: utf-8 -*-
#  Copyleft 2021-2024 Mattijs Snepvangers.
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

from enum import Enum
import time
from multiprocessing import Process

class TaskType(Enum):
    """Enum for different task types."""
    ART_GETTER = "art_getter"
    IMPORTER = "importer"
    TAGGER = "tagger"
    EXPORTER = "exporter"
    LYRICS_GETTER = "lyrics_getter"
    ALBUM_COVER_GETTER = "album_cover_getter"
    NORMALIZER = "normalizer"
    TRIMMER = "trimmer"
    CONVERTER = "converter"
    PARSER = "parser"
    FILE_RENAME = "file_rename"
    FILE_MOVE = "file_move"
    FILE_DELETE = "file_delete"

class TaskStatus(Enum):
    """Enum for different task statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task():
    """Task Parent class to be used by tasks which are managed by TaskManager."""
    processed:int = 0
    batch:dict = {}
    process:Process = None
    task_id:str = None
    task_result:str = None
    task_error:str = None
    task_start_time = None
    task_end_time = None
    task_duration = None
    task_progress:int = 0


    def __init__(self, config, task_name=None, task_type=None):
        """Initializes the Task class."""
        self.config = config
        self.task_name = task_name
        self.task_type = task_type
        self.task_status = TaskStatus.PENDING

    def run(self):
        """
        Runs the task.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def start(self):
        """
        Starts the task.
        """
        self.task_start_time = time.time()
        self.task_status = TaskStatus.RUNNING
        self.process = Process(target=self.run)
        self.process.start()
        return True

    def wait(self):
        """
        Waits for the task to complete.
        """
        if self.process and self.process.is_alive():
            self.process.join()
            self.task_end_time = time.time()
            self.task_duration = self.task_end_time - self.task_start_time
            if self.process.exitcode == 0:
                self.task_status = TaskStatus.COMPLETED
            else:
                self.task_status = TaskStatus.FAILED
                self.task_error = "Task failed"
        return True

    def cancel(self):
        """
        Cancels the task.
        """
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.task_status = TaskStatus.CANCELLED
            self.task_end_time = time.time()
            self.task_duration = self.task_end_time - self.task_start_time
            self.task_progress = 100
            self.task_result = None
            self.task_error = "Task cancelled"
            self.process = None
            return True
        return False

    def get_task_status(self):
        """
        Returns the status of the task.
        """
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_type": self.task_type,
            "task_status": self.task_status,
            "task_result": self.task_result,
            "task_error": self.task_error,
            "task_start_time": self.task_start_time,
            "task_end_time": self.task_end_time,
            "task_duration": self.task_duration,
            "task_progress": self.task_progress
        }

    def set_task_progress(self, progress):
        """
        Sets the progress of the task.
        """
        if 0 <= progress <= 100:
            self.task_progress = progress
            if progress >= 100:
                self.task_status = TaskStatus.COMPLETED
                self.task_end_time = time.time()
                self.task_duration = self.task_end_time - self.task_start_time
            elif progress < 0:
                self.task_progress = 0
            elif progress > 100:
                self.task_progress = 100
            self.task_status = TaskStatus.RUNNING
        else:
            raise ValueError("Progress must be between 0 and 100")

    def get_task_progress(self):
        """
        Returns the progress of the task.
        """
        return self.task_progress

    def get_task_result(self):
        """
        Returns the result of the task.
        """
        return self.task_result or False

    def set_task_result(self, result):
        """
        Sets the result of the task.
        """
        self.task_result = result
        if result is not None:
            self.task_status = TaskStatus.COMPLETED
            self.task_end_time = time.time()
            self.task_duration = self.task_end_time - self.task_start_time
        else:
            self.task_status = TaskStatus.FAILED
            self.task_error = "Task failed"
            self.task_end_time = time.time()
            self.task_duration = self.task_end_time - self.task_start_time
            self.task_progress = 100
            self.process = None
            return True
        return False

    def get_task_error(self):
        """
        Returns the error of the task.
        """
        return self.task_error

    def set_task_error(self, error):
        """
        Sets the error of the task.
        """
        self.task_error = error
        self.task_status = TaskStatus.FAILED
        self.task_end_time = time.time()
        self.task_duration = self.task_end_time - self.task_start_time
        self.task_progress = 100
        self.process = None
        return True

    def get_task_id(self) -> str:
        """
        Returns the task ID.
        """
        return self.task_id

    def set_task_id(self) -> None:
        """
        Sets the task ID.
        """
        self.task_id = self.task_name + "_" + str(int(time.time()))
        self.task_id = self.task_id.replace(" ", "_")

    def get_task_name(self) -> str:
        """
        Returns the task name.
        """
        return self.task_name

    def set_task_status(self, task_status: TaskStatus) -> None:
        """
        Sets the task status.
        """
        self.task_status = task_status
        if task_status == TaskStatus.COMPLETED:
            self.task_end_time = time.time()
            self.task_duration = self.task_end_time - self.task_start_time
        elif task_status == TaskStatus.FAILED:
            self.task_error = "Task failed"
            self.task_end_time = time.time()
            self.task_duration = self.task_end_time - self.task_start_time
            self.task_progress = 100
            self.process = None

    def get_task_type(self) -> str:
        """
        Returns the task type.
        """
        return self.task_type

    def set_task_type(self, task_type: TaskType) -> None:
        """
        Sets the task type.
        """
        if task_type not in TaskType:
            raise ValueError("task_type a valid TaskType")
        self.task_type = task_type

    def set_task_process(self, process: Process|None) -> None:
        """
        Sets the task process.
        """
        self.process = process

    def task_finished(self) -> None:
        """
        Sets the task end time, duration, and progress to 100%.
        Unstes Process and sets the task status to COMPLETED.
        """
        self.task_end_time = time.time()
        self.task_duration = self.task_end_time - self.task_start_time
        self.task_progress = 100
        self.process = None
        self.task_status = TaskStatus.COMPLETED

    def set_progress(self) -> None:
        """
        Sets the progress of the task.

        Args:
            progress: The progress of the task.
        """
        self.processed += 1
        self.task_progress = (self.processed / len(self.batch)) * 100