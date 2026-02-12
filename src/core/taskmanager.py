# src/core/task_manager.py
from __future__ import annotations
import asyncio
import os
import json
from typing import Type, Optional, Any, Dict

from Singletons import DBInstance, Logger
from config import Config
from .registry import registry
from .enums import TaskStatus, TaskType
from .dbmodels import DBTask  # ORM model, NOT a task
from .concurrency import system_exclusive_lock, acquire_exclusive, release_exclusive

logger = Logger()


class TaskManager:
    """
    Async TaskManager that schedules tasks, enforces concurrency limits,
    and respects the system-wide exclusive lock.
    """

    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "TaskManager":
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Allow legacy callers to pass args; singleton init happens in __new__.
        return None

    def _initialize(self) -> None:
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_queue: list[Any] = []
        self.running_tasks = 0
        self.max_concurrent_tasks = 2 * (os.cpu_count() or 2)
        self.db = DBInstance
        self.config = Config.get_sync()
        self.logger = Logger()
        self._shutdown = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._exclusive_holder_task_id: Optional[str] = None

        # auto-discover plugins (async)
        asyncio.create_task(self._discover_and_register_plugins())

        # start monitor
        asyncio.create_task(self._async_start_monitor())

    async def _discover_and_register_plugins(self) -> None:
        await registry.init_all_audioutils()
        # task/classes mapping comes from registry
        self.task_map = registry._task_classes

        self.logger.info("TaskManager: plugin discovery complete.")

    # ---------------- monitor ----------------
    async def _async_start_monitor(self) -> None:
        if self._monitor_task and not self._monitor_task.done():
            return
        self._monitor_task = asyncio.create_task(self._monitor_loop(), name="task_manager.monitor")

    async def shutdown(self) -> None:
        self._shutdown = True
        if self._monitor_task:
            self._monitor_task.cancel()
            await asyncio.gather(self._monitor_task, return_exceptions=True)
        pause_all = getattr(self, "pause_all_running_tasks", None)
        if pause_all is not None:
            await pause_all()

    async def pause_all_running_tasks(self) -> None:
        """Compatibility no-op for legacy shutdown flow."""
        return None

    async def _monitor_loop(self) -> None:
        while not self._shutdown:
            await self._check_running_tasks()
            await asyncio.sleep(1)
        self.logger.info("TaskManager monitor exiting.")

    async def _check_running_tasks(self) -> None:
        """
        Inspect running tasks and update status; release exclusive lock if holder finished.
        This expects each task instance to expose 'is_alive' or 'status' fields as before.
        """
        for status, group in list(self.tasks.items()):
            for task_id, task in list(group.items()):
                # if running but not alive -> finalize
                if getattr(task, "status", None) == TaskStatus.RUNNING and not getattr(task, "is_alive", lambda: True)():
                    try:
                        # call task.wait() if present
                        if hasattr(task, "wait"):
                            await asyncio.get_event_loop().run_in_executor(None, task.wait)
                    except Exception:
                        pass

                    self.running_tasks = max(self.running_tasks - 1, 0)
                    # update status transition logic (task object should update its status)
                    self.update_task_status(task)

                    # if this task held the exclusive lock, release it
                    if getattr(task, "task_id", None) == self._exclusive_holder_task_id:
                        self.logger.info(f"TaskManager: releasing exclusive lock held by {task.task_id}")
                        release_exclusive()
                        self._exclusive_holder_task_id = None

        # start new tasks from queue if possible
        while self.task_queue and self.running_tasks < self.max_concurrent_tasks:
            task = self.task_queue.pop(0)
            await self._start_task(task, "Queued task ")
            self.update_task_status(task)

    # ---------------- persistence ----------------
    async def _save_task_to_db(self, task: Any) -> None:
        if getattr(task, "is_idle_task", False):
            return
        if not getattr(task, "task_id", None):
            raise ValueError("Task must have task_id before saving")
        db_task = DBTask()
        db_task.import_task(task)
        async for session in self.db.get_session():
            session.add(db_task)
            await session.commit()
            await session.close()

    # ---------------- registration helpers ----------------
    def register_task(self, task: Any) -> None:
        status = getattr(task, "status", TaskStatus.PENDING).value
        if status not in self.tasks:
            self.tasks[status] = {}
        self.tasks[status][task.task_id] = task

    def unregister_task(self, task_id: str, status: TaskStatus) -> None:
        if status.value in self.tasks and task_id in self.tasks[status.value]:
            del self.tasks[status.value][task_id]

    def update_task_status(self, task: Any) -> None:
        self.unregister_task(getattr(task, "task_id"), getattr(task, "old_status", TaskStatus.PENDING))
        self.register_task(task)

    def get_task(self, task_id: str) -> Optional[Any]:
        return next(
            (task_group[task_id] for task_group in self.tasks.values() if task_id in task_group),
            None,
        )

    # ---------------- exclusivity helpers ----------------
    async def _wait_if_exclusive_active(self) -> None:
        """If an exclusive processor/task holds the lock, wait until it is released."""
        while system_exclusive_lock.locked():
            await asyncio.sleep(0.1)

    # ---------------- factories / start ----------------
    async def start_task(
        self,
        task_class: Type[Any],
        batch: Any = None,
        kwargs: Optional[dict] = None,
    ) -> str:
        """
        Instantiate and start (or queue) a task.
        This method respects the global exclusive lock:
          - If the task instance is exclusive: it acquires the lock for the duration of the task run.
          - If non-exclusive: it will wait while an exclusive holder runs.
        """

        kwargs = kwargs or {}
        # instantiate via registry
        # registry.create_task returns an instance with audioutil deps injected
        task = await registry.create_task(
            task_class.name,
            batch=batch,
            config=(self.config or Config.get_sync()),
            **kwargs,
        )

        # register
        self.register_task(task)

        # Wait for exclusive processors/tasks to finish if this task is not exclusive
        if not getattr(task, "exclusive", False):
            await self._wait_if_exclusive_active()

        # handle mutual exclusion and queueing as before
        if getattr(task, "task_type", None) in getattr(self, "exclusive_task_types", set()):
            # if one of the task types is globally exclusive, queue if another instance running
            if self._exclusive_task_running(task.task_type):
                self.task_queue.append(task)
                self.logger.info(f"Task {task.task_id} queued (mutually exclusive running).")
                return task.task_id

        if getattr(task, "exclusive", False):
            # Acquire the system-wide exclusive lock for the duration of this task.
            await acquire_exclusive()
            # record which task holds the lock; released when task finishes (monitor loop will release)
            self._exclusive_holder_task_id = task.task_id

        # Queue on concurrency limits
        if self.running_tasks >= self.max_concurrent_tasks:
            self.task_queue.append(task)
            self.logger.info(f"Task {task.task_id} queued (concurrency limit).")
            return task.task_id

        # Start the task (non-blocking; task.start() should be implemented to run in background if needed)
        await self._start_task(task, "Task ")
        await self._save_task_to_db(task)
        return task.task_id

    async def _start_task(self, task: Any, task_desc: str) -> None:
        """Start the task instance (in-process)."""
        # Implementation detail: if task.start is async, schedule it as a background task.
        start_fn = getattr(task, "start", None)
        if start_fn is None:
            # maybe older callable interface
            if hasattr(task, "run"):
                # schedule run() in background
                asyncio.create_task(task.run(), name=f"task:{task.task_id}")
            else:
                raise RuntimeError("Task object has no start/run method")
        else:
            # schedule start() as background task (don't await here)
            asyncio.create_task(start_fn(), name=f"task:{task.task_id}")

        self.running_tasks += 1
        self.logger.info(f"{task_desc}{getattr(task, 'task_id', '<unknown>')} started.")

    # ---------------- resume / restore ----------------
    async def resume_tasks(self) -> None:
        """Resume paused tasks from DB (if any)."""
        paused_tasks = await self.db.get_paused_tasks()
        for record in paused_tasks:
            try:
                task_type = TaskType(record.task_type)
                batch = record.get_batch()
                kwargs = json.loads(record.kwargs or "{}")
                task_class = self._get_task_class(task_type)
                await self.start_task(task_class, batch=batch, kwargs=kwargs)
            except Exception as e:
                self.logger.error(f"Failed to resume task {record.task_id}: {e}")

    def _get_task_class(self, task_type: TaskType) -> Type[Any]:
        """
        Map TaskType -> registered task class. The registry keeps track of task classes by name;
        we use task_type.name lowercase to find the class, or rely on an explicit mapping if you provided one.
        """
        # Prefer a direct mapping if available
        tm = getattr(self, "task_map", {})
        # search by TaskType member name or by string
        for cls_name, cls in tm.items():
            if getattr(cls, "task_type", None) == task_type:
                return cls
        raise ValueError(f"No task class mapped for {task_type}")

    def _exclusive_task_running(self, task_type: TaskType) -> bool:
        for task_group in self.tasks.values():
            for task in task_group.values():
                if getattr(task, "task_type", None) == task_type and getattr(task, "status", None) == TaskStatus.RUNNING:
                    return True
        return False

    def set_exclusive_task_types(self, exclusive_types: list[TaskType]) -> None:
        self.exclusive_task_types = set(exclusive_types)
