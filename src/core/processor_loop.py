# src/core/processor_loop.py
"""
Processor loop that runs registered processors and schedules emitted tasks.

This runner:
 - Instantiates all processors registered in the central registry
 - Runs each processor in a background asyncio.Task
 - Enforces the system-wide exclusive lock:
    * If a processor sets `exclusive = True`, the loop will acquire the
      system_exclusive_lock for the *duration of that processor's run()*
    * Non-exclusive processors will wait for the lock to be released before they start
 - Collects emitted task records via ProcessorBase.pop_emitted() and instructs TaskManager to schedule them.
"""

from __future__ import annotations
import asyncio
from typing import Any, List, Tuple

from Singletons import Logger
from .registry import registry as default_registry
from .taskmanager import TaskManager

logger = Logger()


class ProcessorLoop:
    def __init__(self, *, registry: Any = None, config: Any = None) -> None:
        self.registry = registry or default_registry
        self.config: Any = config
        self._processors: List[Tuple[Any, asyncio.Task[Any]]] = []
        self._shutdown = False
        self.task_manager = TaskManager()  # uses the async TaskManager below

    async def start_all(self) -> None:
        """Instantiate and run all registered processors (non-blocking)."""
        for name, cls in self.registry._processor_classes.items():
            try:
                inst = await self.registry.create_processor(name, config=self.config)
                t = asyncio.create_task(self._run_processor_instance(inst), name=f"processor:{name}")
                self._processors.append((inst, t))
                logger.info(f"ProcessorLoop: started processor {name}")
            except Exception as e:
                logger.error(f"ProcessorLoop: failed to create/start {name}: {e}")

    async def _run_processor_instance(self, inst: Any) -> None:
        """
        Runs a single processor instance in a loop. Each invocation of
        inst() (which may run until completion) is surrounded by
        concurrency coordination.
        """
        while not self._shutdown:
            try:
                acquired = await inst.acquire_concurrency()
                if not acquired:
                    await asyncio.sleep(0.1)
                    continue
                try:
                    await inst()
                finally:
                    inst.release_concurrency()

            except asyncio.CancelledError:
                # graceful shutdown
                break
            except Exception as e:
                logger.exception(f"Processor {getattr(inst, 'name', repr(inst))} crashed: {e}")

            # After each run(), pick up emitted tasks and schedule them
            try:
                emitted = getattr(inst, "collect_emitted_tasks", lambda: [])()
                for rec in emitted:
                    try:
                        task_type = rec["task_type"]
                        batch = rec.get("batch")
                        extra = rec.get("extra", {})
                        task_cls = self.task_manager._get_task_class(task_type)
                        await self.task_manager.start_task(task_cls, batch=batch, kwargs=extra)
                    except Exception as e:
                        logger.error(f"ProcessorLoop: Failed to schedule emitted task {rec}: {e}")
            except Exception as e:
                logger.debug(f"ProcessorLoop: error while handling emitted tasks: {e}")

            # small sleep to avoid tight loop; processors choose to sleep inside run() as needed
            await asyncio.sleep(0.1)

    async def shutdown(self) -> None:
        self._shutdown = True
        for inst, task in self._processors:
            try:
                inst.stop()
            except Exception:
                pass
        # give them a moment to stop
        await asyncio.sleep(0.1)
        for inst, task in self._processors:
            if not task.done():
                task.cancel()
        # wait for cancellations
        await asyncio.gather(*(t for _, t in self._processors), return_exceptions=True)
        self._processors.clear()
