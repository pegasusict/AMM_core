# src/core/task_manager.py
from __future__ import annotations
import asyncio
import os
import time
from typing import Any, Dict, List, Optional

from ..Singletons import Logger
from .registry import registry
from .enums import StageType

logger = Logger  # global singleton

# configurable defaults
DEFAULT_SYSTEM_LOAD_LIMIT = 15.0
DEFAULT_HEAVY_IO_CONCURRENCY = max(1, (os.cpu_count() or 2) // 2)  # conservative
DEFAULT_NORMAL_CONCURRENCY = max(2, 2 * (os.cpu_count() or 2))
NORMAL_TASK_BACKOFF_SEC = 1.0
NORMAL_TASK_MAX_WAIT_SEC = 30.0


class TaskManager:
    """
    Registry-driven TaskManager:
      - Uses registry.create_task/create_processor (DI handled by registry)
      - Schedules by stage_type using registry._stage_records
      - Enforces exclusive and heavy_io semantics
      - Observes OS load average to throttle heavy work
      - Runs processors (including idle_runner) separately
    """

    def __init__(
        self,
        *,
        system_load_limit: float = DEFAULT_SYSTEM_LOAD_LIMIT,
        max_normal_tasks: int = DEFAULT_NORMAL_CONCURRENCY,
        max_heavy_io: int = DEFAULT_HEAVY_IO_CONCURRENCY,
        idle_interval: float = 300.0,
    ):
        self.system_load_limit = float(system_load_limit)
        self.max_normal_tasks = int(max_normal_tasks)
        self.max_heavy_io = int(max_heavy_io)
        self.idle_interval = float(idle_interval)

        # concurrency primitives
        self._normal_sem = asyncio.Semaphore(self.max_normal_tasks)
        self._heavy_sem = asyncio.Semaphore(self.max_heavy_io)

        # exclusive semantics: one running instance per TaskType
        self._exclusive_locks: Dict[str, asyncio.Lock] = {}

        # currently running task instances keyed by task_id
        self._running: Dict[str, Any] = {}

        # background idle runner task
        self._idle_task: Optional[asyncio.Task] = None
        self._last_activity_ts = time.time()

        # control flags
        self._shutdown = False

    # --------------------------
    # System load helpers
    # --------------------------
    def _get_load(self) -> float:
        try:
            return float(os.getloadavg()[0])
        except Exception:
            return 0.0

    def _is_load_high(self) -> bool:
        return self._get_load() > self.system_load_limit

    # --------------------------
    # Exclusive lock helpers
    # --------------------------
    def _get_exclusive_lock_for(self, task_type_name: str) -> asyncio.Lock:
        if task_type_name not in self._exclusive_locks:
            self._exclusive_locks[task_type_name] = asyncio.Lock()
        return self._exclusive_locks[task_type_name]

    # --------------------------
    # Public lifecycle
    # --------------------------
    def start_idle_loop(self):
        """Start the idle_runner background coroutine if present."""
        if self._idle_task is not None and not self._idle_task.done():
            return
        self._idle_task = asyncio.create_task(self._idle_loop())
        logger.info("TaskManager: idle loop started")

    async def shutdown(self):
        """Stop accepting new work and wait for running tasks to finish."""
        self._shutdown = True
        if self._idle_task:
            self._idle_task.cancel()
            try:
                await self._idle_task
            except asyncio.CancelledError:
                pass

        # wait for running tasks to finish (best-effort)
        start = time.time()
        while self._running and (time.time() - start) < 30:
            await asyncio.sleep(0.1)

    # --------------------------
    # Task execution primitives
    # --------------------------
    async def _run_task_instance(self, task_instance) -> None:
        """
        Runs the task instance (no args). Catches/logs exceptions.
        """
        tid = getattr(task_instance, "task_id", f"{task_instance.name}:{id(task_instance)}")
        self._running[tid] = task_instance
        self._last_activity_ts = time.time()
        logger.info(f"TaskManager: starting task {task_instance.name} ({tid})")

        try:
            # prefer task.run() as tasks manage batches internally
            await task_instance.run()
            logger.info(f"TaskManager: finished task {task_instance.name} ({tid})")
        except Exception as exc:
            logger.exception(f"TaskManager: task {task_instance.name} ({tid}) raised: {exc}")
            # allow tasks to set their own error state; we just log
        finally:
            self._running.pop(tid, None)
            self._last_activity_ts = time.time()

    async def _maybe_wait_for_normal_capacity(self) -> bool:
        """
        Wait (with bounded backoff) until normal semaphore is available if load is high.
        Returns True if succeeded and we should proceed, False if timed out and should skip.
        """
        waited = 0.0
        while self._is_load_high() and waited < NORMAL_TASK_MAX_WAIT_SEC:
            await asyncio.sleep(NORMAL_TASK_BACKOFF_SEC)
            waited += NORMAL_TASK_BACKOFF_SEC
        return not self._is_load_high()

    async def _execute_with_constraints(self, create_instance_coro, *, exclusive: bool, heavy_io: bool, task_type_name: Optional[str]):
        """
        create_instance_coro: coroutine that returns an instantiated task (registry.create_task)
        Enforces:
          - system load checks
          - heavy_io semaphore
          - normal semaphore
          - exclusive per task_type (if provided)
        """
        # If system load high and heavy_io then skip immediately
        if heavy_io and self._is_load_high():
            logger.info("TaskManager: skipping heavy_io task due to high system load")
            return None  # skip

        # For non-exclusive normal tasks, when load is high, wait a bit (bounded)
        if not exclusive and not heavy_io and self._is_load_high():
            ok = await self._maybe_wait_for_normal_capacity()
            if not ok:
                logger.info("TaskManager: skipping non-exclusive task after backoff due to sustained high load")
                return None  # skip

        # Acquire semaphores/locks then run
        exclusive_lock = None
        if exclusive and task_type_name:
            exclusive_lock = self._get_exclusive_lock_for(task_type_name)

        # choose semaphores
        sem = self._heavy_sem if heavy_io else self._normal_sem

        # acquire in fair order: exclusive lock (if any) -> sem
        # use async context managers
        async def _acquire_and_run():
            async with sem:
                # exclusive_lock ensures only one of the same task_type runs concurrently
                if exclusive_lock:
                    async with exclusive_lock:
                        inst = await create_instance_coro()
                        if inst is None:
                            return None
                        await self._run_task_instance(inst)
                        return inst
                else:
                    inst = await create_instance_coro()
                    if inst is None:
                        return None
                    await self._run_task_instance(inst)
                    return inst

        # run and return instance (or None if skipped)
        return await _acquire_and_run()

    # --------------------------
    # High-level APIs
    # --------------------------
    async def run_task(self, task_name: str, *, batch: Any = None, config: Any = None, **kwargs) -> Optional[Any]:
        """
        Instantiate via registry.create_task and run it while respecting constraints.
        Returns the task instance or None if skipped.
        """
        # get class-level flags by name -> prefer registry.get_task_class if available
        cls = registry.get_task_class(task_name)
        if cls is None:
            logger.error(f"TaskManager: unknown task '{task_name}'")
            return None

        exclusive = bool(getattr(cls, "exclusive", False))
        heavy_io = bool(getattr(cls, "heavy_io", False))
        task_type = getattr(cls, "task_type", None)
        task_type_name = task_type.name if task_type is not None else None

        # coroutine to create instance (registry will inject audio utils)
        async def _create():
            try:
                return await registry.create_task(task_name, batch=batch, config=(config or registry.Config()), **kwargs)
            except Exception as e:
                logger.exception(f"TaskManager: failed to instantiate task {task_name}: {e}")
                return None

        return await self._execute_with_constraints(_create, exclusive=exclusive, heavy_io=heavy_io, task_type_name=task_type_name)

    async def run_stage(self, stage: StageType, *, batch: Any = None, config: Any = None):
        """
        Run all tasks declared for a StageType in registration order.
        The registry's _stage_records is authoritative (maps stage -> [task_names]).
        This method does not pass data; tasks operate on batches internally.
        """
        # allow stage being an enum etc.
        stage_key = getattr(stage, "value", stage)
        task_names: List[str] = registry._stage_records.get(stage_key, [])
        if not task_names:
            logger.debug(f"TaskManager: no tasks for stage {stage_key}")
            return

        logger.info(f"TaskManager: running stage {stage_key} with {len(task_names)} task(s)")

        # Run tasks sequentially in registration order but each task internal concurrency is managed
        for tname in task_names:
            if self._shutdown:
                logger.info("TaskManager: shutdown requested, stopping stage execution")
                break

            await self.run_task(tname, batch=batch, config=config)

    # --------------------------
    # Processor APIs
    # --------------------------
    async def run_processor(self, processor_name: str, *, config: Any = None, **kwargs):
        """
        Instantiate and run a processor. Processors do not accept pipeline/batch args
        from TaskManager — they manage their own inputs if any.
        """
        cls = registry.get_processor_class(processor_name)
        if cls is None:
            logger.error(f"TaskManager: unknown processor '{processor_name}'")
            return None

        heavy_io = bool(getattr(cls, "heavy_io", False))
        exclusive = bool(getattr(cls, "exclusive", False))
        task_type = getattr(cls, "task_type", None)
        task_type_name = task_type.name if task_type is not None else None

        async def _create_proc():
            try:
                return await registry.create_processor(processor_name, config=(config or registry.Config()), **kwargs)
            except Exception as e:
                logger.exception(f"TaskManager: failed to instantiate processor {processor_name}: {e}")
                return None

        return await self._execute_with_constraints(_create_proc, exclusive=exclusive, heavy_io=heavy_io, task_type_name=task_type_name)

    async def run_all_processors(self):
        """Run all registered processors in registry (excluding idle_runner)."""
        for pname in registry.list_registered().get("processors", []):
            if pname == "idle_runner":
                continue
            await self.run_processor(pname)

    # --------------------------
    # Idle runner loop
    # --------------------------
    async def _idle_loop(self):
        """
        Background loop that triggers the idle_runner processor when
        TaskManager has been idle for idle_interval seconds.
        """
        while not self._shutdown:
            try:
                now = time.time()
                idle_time = now - self._last_activity_ts
                if idle_time >= self.idle_interval:
                    if "idle_runner" in registry.list_registered().get("processors", []):
                        logger.debug("TaskManager: triggering idle_runner")
                        await self.run_processor("idle_runner")
                        # update activity timestamp after idle_runner runs
                        self._last_activity_ts = time.time()
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception(f"TaskManager: idle loop error: {exc}")
                await asyncio.sleep(1.0)

    # --------------------------
    # Helpers / monitoring
    # --------------------------
    def running_tasks(self) -> int:
        return len(self._running)

    def is_idle(self) -> bool:
        return self.running_tasks() == 0

    # convenience wrapper to trigger stages in sequence
    async def run_pipeline(self, stage_order: List[StageType], *, batch: Any = None, config: Any = None):
        """
        Execute stages in order. Tasks manage batches internally.
        """
        for stage in stage_order:
            if self._shutdown:
                break
            await self.run_stage(stage, batch=batch, config=config)
