# src/core/task_manager.py
from __future__ import annotations
import asyncio
import os
import json
from typing import Type, Optional, Any, Dict

from sqlmodel import select
from Singletons import DBInstance, Logger
from config import Config
from .bootstrap import bootstrap_plugins
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
        self._runner_tasks: Dict[str, asyncio.Task[Any]] = {}

        # auto-discover plugins (async)
        asyncio.create_task(self._discover_and_register_plugins())

        # start monitor
        asyncio.create_task(self._async_start_monitor())

    async def _discover_and_register_plugins(self) -> None:
        await bootstrap_plugins()
        await registry.init_all_audioutils()
        # task/classes mapping comes from registry
        self.task_map = registry._task_classes # type: ignore

        self.logger.info("TaskManager: plugin discovery complete.")

    # ---------------- monitor ----------------
    async def _async_start_monitor(self) -> None:
        if self._monitor_task and not self._monitor_task.done(): # type: ignore
            return
        self._monitor_task = asyncio.create_task(self._monitor_loop(), name="task_manager.monitor")

    async def shutdown(self) -> None:
        self._shutdown = True
        if self._monitor_task: # type: ignore
            self._monitor_task.cancel() # type: ignore
            await asyncio.gather(self._monitor_task, return_exceptions=True) # type: ignore
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
        Inspect running tasks and persist lifecycle updates.
        """
        finalized_ids: set[str] = set()
        for status_key, group in list(self.tasks.items()):
            for task_id, task in list(group.items()):
                await self._process_task_lifecycle(status_key, task_id, task, finalized_ids)

        await self._drain_task_queue()

    async def _process_task_lifecycle(
        self,
        status_key: str,
        task_id: str,
        task: Any,
        finalized_ids: set[str],
    ) -> None:
        self._sync_task_status(status_key, task)
        runner = self._runner_tasks.get(task_id)
        if not self._runner_ready(task_id, runner, finalized_ids):
            return

        finalized_ids.add(task_id)
        await self._await_runner(task_id, task, runner)
        self._runner_tasks.pop(task_id, None)
        self._finalize_task(task)
        await self._save_task_to_db(task)

    def _sync_task_status(self, status_key: str, task: Any) -> None:
        status = getattr(task, "status", TaskStatus.PENDING)
        status_value = status.value if isinstance(status, TaskStatus) else str(status)
        if status_value != status_key:
            self.update_task_status(task)

    def _runner_ready(
        self,
        task_id: str,
        runner: Optional[asyncio.Task],
        finalized_ids: set[str],
    ) -> bool:
        return runner is not None and task_id not in finalized_ids and runner.done()

    async def _await_runner(self, task_id: str, task: Any, runner: asyncio.Task) -> None:
        try:
            await runner
        except asyncio.CancelledError:
            if hasattr(task, "cancel"):
                task.cancel()
        except Exception as exc:
            self.logger.exception(f"Task {task_id} raised an unhandled exception: {exc}")
            if getattr(task, "status", None) != TaskStatus.FAILED and hasattr(task, "set_error"):
                task.set_error(str(exc))

    def _finalize_task(self, task: Any) -> None:
        self.running_tasks = max(self.running_tasks - 1, 0)
        self.update_task_status(task)
        self._release_exclusive_if_holder(task)

    def _release_exclusive_if_holder(self, task: Any) -> None:
        if getattr(task, "task_id", None) != self._exclusive_holder_task_id:
            return
        self.logger.info(f"TaskManager: releasing exclusive lock held by {task.task_id}")
        release_exclusive()
        self._exclusive_holder_task_id = None

    async def _drain_task_queue(self) -> None:
        while self.task_queue and self.running_tasks < self.max_concurrent_tasks:
            task = self.task_queue.pop(0)
            await self._start_task(task, "Queued task ")
            await asyncio.sleep(0)
            await self._save_task_to_db(task)
            self.update_task_status(task)

    # ---------------- persistence ----------------
    async def _save_task_to_db(self, task: Any) -> None:
        if getattr(task, "is_idle_task", False):
            return
        if not getattr(task, "task_id", None):
            raise ValueError("Task must have task_id before saving")
        async for session in self.db.get_session():
            result = await session.exec(select(DBTask).where(DBTask.task_id == task.task_id))
            db_task = result.first()
            if db_task is None:
                db_task = DBTask()
            db_task.import_task(task, attach_relations=False)
            session.add(db_task)
            await session.commit()

    # ---------------- registration helpers ----------------
    def register_task(self, task: Any) -> None:
        task_id = getattr(task, "task_id", None)
        if not task_id:
            return

        # Keep a single canonical location for each task_id.
        for group in self.tasks.values():
            group.pop(task_id, None)

        status = getattr(task, "status", TaskStatus.PENDING)
        status_key = status.value if isinstance(status, TaskStatus) else str(status)
        if status_key not in self.tasks:
            self.tasks[status_key] = {}
        self.tasks[status_key][task_id] = task

    def unregister_task(self, task_id: str, status: TaskStatus) -> None:
        if status.value in self.tasks and task_id in self.tasks[status.value]:
            del self.tasks[status.value][task_id]

    def update_task_status(self, task: Any) -> None:
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
        kwargs: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Instantiate and start (or queue) a task.
        This method respects the global exclusive lock:
          - If the task instance is exclusive: it acquires the lock for the duration of the task run.
          - If non-exclusive: it will wait while an exclusive holder runs.
        """

        kwargs = kwargs or {} # type: ignore
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
                await self._save_task_to_db(task)
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
            await self._save_task_to_db(task)
            self.logger.info(f"Task {task.task_id} queued (concurrency limit).")
            return task.task_id

        # Start the task (non-blocking; task.start() should be implemented to run in background if needed)
        await self._start_task(task, "Task ")
        await asyncio.sleep(0)
        self.update_task_status(task)
        await self._save_task_to_db(task)
        return task.task_id

    async def _start_task(self, task: Any, task_desc: str) -> None:
        """Start the task instance (in-process)."""
        # Implementation detail: if task.start is async, schedule it as a background task.
        start_fn = getattr(task, "start", None)
        runner_task: asyncio.Task[Any]
        if start_fn is None:
            # maybe older callable interface
            run_fn = getattr(task, "run", None)
            if run_fn is not None:
                if asyncio.iscoroutinefunction(run_fn):
                    runner_task = asyncio.create_task(run_fn(), name=f"task:{task.task_id}")
                else:
                    runner_task = asyncio.create_task(asyncio.to_thread(run_fn), name=f"task:{task.task_id}")
            else:
                raise RuntimeError("Task object has no start/run method")
        else:
            # schedule start() as background task (don't await here)
            if asyncio.iscoroutinefunction(start_fn):
                runner_task = asyncio.create_task(start_fn(), name=f"task:{task.task_id}")
            else:
                runner_task = asyncio.create_task(asyncio.to_thread(start_fn), name=f"task:{task.task_id}")

        self._runner_tasks[task.task_id] = runner_task
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
                await self.start_task(task_class, batch=batch, kwargs=kwargs) # type: ignore
            except Exception as e:
                self.logger.error(f"Failed to resume task {record.task_id}: {e}")

    def _get_task_class(self, task_type: TaskType) -> Type[Any]:
        """
        Map TaskType -> registered task class. The registry keeps track of task classes by name;
        we use task_type.name lowercase to find the class, or rely on an explicit mapping if you provided one.
        """
        # Prefer a direct mapping if available
        tm = getattr(self, "task_map", {}) or {}
        # search by TaskType member name or by string
        for cls_name, cls in tm.items(): # type: ignore
            if getattr(cls, "task_type", None) == task_type:
                return cls
        # Fallback: registry may already know task classes even if task_map init raced.
        for cls_name, cls in registry._task_classes.items(): # type: ignore[attr-defined]
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
