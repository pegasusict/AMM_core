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


import json
import os
import time
from threading import Thread
from typing import Callable, Any, Optional, Set, Type

from art_getter import ArtGetter
from importer import Importer
from converter import Converter
from deduper import Deduper
from exporter import Exporter
from fingerprinter import FingerPrinter
from lyrics_getter import LyricsGetter
from normalizer import Normalizer
from parser import Parser
from sorter import Sorter
from tagger import Tagger
from trimmer import Trimmer

from ..Singletons.logger import Logger
from ..Singletons.database import DB
from ..Singletons.config import Config
from ..models import DBTask
from ..Enums import TaskStatus, TaskType
from .task import Task


class TaskManager:
    """Manages tasks with a concurrency limit of 2 per CPU core."""

    _instance = None

    def __new__(cls):
        """Takes care of the singleton instance of TaskManager."""
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initializes the TaskManager instance."""
        self.tasks: dict[str, dict[str, Task]] = {}
        self.task_queue: list[Task] = []
        self.running_tasks = 0
        self.max_concurrent_tasks = 2 * (os.cpu_count() or 2)  # Default to 2 if cpu_count() is None
        self.exclusive_task_types: Set[TaskType] = set(
            [
                TaskType.IMPORTER,
                TaskType.TAGGER,
                TaskType.FINGERPRINTER,
                TaskType.EXPORTER,
                TaskType.NORMALIZER,
                TaskType.DEDUPER,
                TaskType.TRIMMER,
                TaskType.CONVERTER,
                TaskType.PARSER,
                TaskType.SORTER,
            ]
        )
        self.db = DB()
        self.config = Config()
        self.logger = Logger(self.config)

        # Background thread to monitor tasks
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _monitor_loop(self):
        """Background thread to check for completed tasks and start queued ones."""
        while True:
            self._check_running_tasks()
            time.sleep(1)

    def _check_running_tasks(self):
        for _, group in list(self.tasks.items()):
            for _, task in list(group.items()):
                if task.status == TaskStatus.RUNNING and not task.is_alive():
                    task.wait()
                    self.running_tasks = max(self.running_tasks - 1, 0)
                    self.update_task_status(task)

        # Start next tasks from queue
        while self.task_queue and self.running_tasks < self.max_concurrent_tasks:
            task = self.task_queue.pop(0)
            task.start()
            self.running_tasks += 1
            self.logger.info(f"Queued task {task.task_id} started.")
            self.update_task_status(task)

    def set_exclusive_task_types(self, exclusive_types: list[TaskType]):
        """Set which TaskTypes are limited to a single running instance."""
        self.exclusive_task_types = set(exclusive_types)

    def register_task(self, task: Task):
        status = task.status.value
        if status not in self.tasks:
            self.tasks[status] = {}
        self.tasks[status][task.task_id] = task

    def unregister_task(self, task_id: str, status: TaskStatus):
        if status.value in self.tasks and task_id in self.tasks[status.value]:
            del self.tasks[status.value][task_id]

    def update_task_status(self, task: Task):
        self.unregister_task(task.task_id, task.old_status)
        self.register_task(task)

    def get_task(self, task_id: str) -> Optional[Task]:
        for task_group in self.tasks.values():
            if task_id in task_group:
                return task_group[task_id]
        return None

    def exclusive_task_running(self, task_type: TaskType) -> bool:
        """Check if an exclusive task type is currently running."""
        for task_group in self.tasks.values():
            for task in task_group.values():
                if task.task_type == task_type and task.status == TaskStatus.RUNNING:
                    return True
        return False

    def start_task(
        self,
        task_class: Type[Task],
        task_type: TaskType,
        batch: Any,
        target: Optional[Callable] = None,
        kwargs: Optional[dict[str, Any]] = None,
    ) -> str:
        """Creates and starts (or queues) a new task."""

        task = task_class(config=self.config, task_type=task_type)
        task.batch = batch
        if target:
            task.target = target
        if kwargs:
            for k, v in kwargs.items():
                setattr(task, k, v)

        self.register_task(task)

        # Check if task type is exclusive and already running
        if task.task_type in self.exclusive_task_types:
            if self.exclusive_task_running(task.task_type):
                self.logger.info(f"Task {task.task_id} is exclusive and another task of type {task.task_type} is already running.")
                # Queue the task if an exclusive type is already running
                self.task_queue.append(task)
                return task.task_id

        if self.running_tasks < self.max_concurrent_tasks:
            task.start()
            self.running_tasks += 1
            self.logger.info(f"Task {task.task_id} started.")
        else:
            self.task_queue.append(task)
            self.logger.info(f"Task {task.task_id} queued (limit reached).")

        # Optionally persist to DB
        self.save_task_to_db(task)

        return task.task_id

    def save_task_to_db(self, task: Task):
        """Saves the task to the database."""
        if not isinstance(task, Task):
            raise TypeError("task must be an instance of Task")
        if not task.task_id:
            raise ValueError("task_id must be set before saving to DB")
        db_task = DBTask()
        db_task.import_task(task)
        session = self.db.get_session()
        session.add(db_task)
        session.commit()
        session.close()

    def list_tasks(self) -> list[dict[str, TaskStatus | str | bool | float]]:
        """
        Returns a list of all tasks with basic info:
        - task_id
        - status
        - alive (is process still running)
        - progress
        """
        result = []
        for status, group in self.tasks.items():
            for task in group.values():
                result.append(
                    {
                        "task_id": task.task_id,
                        "status": status,
                        "alive": task.is_alive(),
                        "progress": task.progress,
                    }
                )
        return result


def resume_tasks(self):
    self.logger.info("Resuming paused tasks from database...")

    paused_tasks = self.db.get_paused_tasks()
    for record in paused_tasks:
        try:
            task_type = TaskType(record.task_type)
            batch = record.get_batch() if hasattr(record, "get_batch") else json.loads(record.batch)
            kwargs = json.loads(record.kwargs or "{}")

            # You need to know which task class to use — map or store it
            task_class = self._get_task_class(task_type)
            task = task_class(config=self.config, task_type=task_type)
            task.batch = batch
            for k, v in kwargs.items():
                setattr(task, k, v)

            self.logger.info(f"Resuming task {record.id}")
            self.register_task(task)

            if task_type in self.exclusive_task_types:
                self.task_queue.append(task)
            elif self.running_tasks < self.max_concurrent_tasks:
                task.start()
                self.running_tasks += 1
            else:
                self.task_queue.append(task)

        except Exception as e:
            self.logger.error(f"Failed to resume task {record.id}: {e}")


def _get_task_class(self, task_type: TaskType) -> type[Task]:
    # You must fill in this mapping with your task types and classes
    task_map = {
        TaskType.ART_GETTER: ArtGetter,
        TaskType.CONVERTER: Converter,
        TaskType.DEDUPER: Deduper,
        TaskType.EXPORTER: Exporter,
        TaskType.FINGERPRINTER: FingerPrinter,
        TaskType.IMPORTER: Importer,
        TaskType.LYRICS_GETTER: LyricsGetter,
        TaskType.NORMALIZER: Normalizer,
        TaskType.PARSER: Parser,
        TaskType.SORTER: Sorter,
        TaskType.TAGGER: Tagger,
        TaskType.TRIMMER: Trimmer,
    }
    if task_type not in task_map:
        raise ValueError(f"No task class mapped for {task_type}")
    return task_map[task_type]
