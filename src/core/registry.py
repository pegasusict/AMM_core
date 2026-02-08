# src/core/registry.py
from __future__ import annotations
import asyncio
import inspect
from typing import Any, Dict, List, Optional, Sequence, Type

from Singletons import Logger
from config import Config
from .stage import Stage
from .enums import StageType

logger = Logger()

class PluginRegistry:
    """Unified registry for AudioUtils, Tasks, Processors and Stages."""

    def __init__(self) -> None:
        # classes (populated by decorators at import time)
        self._audioutil_classes: Dict[str, Type[Any]] = {}
        self._task_classes: Dict[str, Type[Any]] = {}
        self._processor_classes: Dict[str, Type[Any]] = {}
        self._stage_records: Dict[str, dict] = {}  # key: stage_name -> meta

        # runtime instances (created on init_all or on demand)
        self._audioutil_instances: Dict[str, Any] = {}
        self._task_instances: Dict[str, Any] = {}
        self._processor_instances: Dict[str, Any] = {}

        # locks for async init
        self._init_lock = asyncio.Lock()
        self._util_locks: Dict[str, asyncio.Lock] = {}

    # ---------------- registration (called by decorators) ----------------
    def register_audioutil(self, cls: Type[Any]) -> None:
        name = getattr(cls, "name", cls.__name__).lower()
        self._audioutil_classes[name] = cls
        logger.debug(f"Registered AudioUtil class: {name}")

    def register_task(self, cls: Type[Any]) -> None:
        name = getattr(cls, "name", cls.__name__).lower()
        self._task_classes[name] = cls
        logger.debug(f"Registered Task class: {name}")
        # auto-register a stage mapping if task defines stage_type/name
        stage_type = getattr(cls, "stage_type", None)
        if stage_type is not None:
            self._stage_records.setdefault(stage_type, []).append(name)
            stage_name = getattr(cls, "stage_name", None) or getattr(cls, "name", None) or cls.__name__
            stage_registry.register_stage(Stage(name=stage_name, stage_type=stage_type))

    def register_processor(self, cls: Type[Any]) -> None:
        name = getattr(cls, "name", cls.__name__).lower()
        self._processor_classes[name] = cls
        logger.debug(f"Registered Processor class: {name}")

    def register_stage(self, stage_name: str, stage_meta: dict) -> None:
        # stage_name can be same as task name or custom
        self._stage_records.setdefault(stage_meta["stage_type"], []).append(stage_name)
        logger.debug(f"Registered Stage: {stage_name} under {stage_meta['stage_type']}")

    # ---------------- audio util instantiation ----------------
    async def _instantiate_audioutil(self, name: str) -> Optional[Any]:
        name = name.lower()
        if name in self._audioutil_instances:
            return self._audioutil_instances[name]

        lock = self._util_locks.setdefault(name, asyncio.Lock())
        async with lock:
            if name in self._audioutil_instances:
                return self._audioutil_instances[name]
            cls = self._audioutil_classes.get(name)
            if not cls:
                logger.error(f"AudioUtil class not found: {name}")
                return None
            try:
                # prefer class.create_async() if present
                create_async = getattr(cls, "create_async", None)
                if create_async and inspect.iscoroutinefunction(create_async):
                    inst = await create_async()
                else:
                    inst = cls()  # normal ctor
                    init_fn = getattr(inst, "init", None)
                    if init_fn and inspect.iscoroutinefunction(init_fn):
                        await init_fn()
                self._audioutil_instances[name] = inst
                logger.info(f"Initialized AudioUtil instance: {name}")
                return inst
            except Exception as e:
                logger.error(f"Failed to initialize audioutil {name}: {e}")
                return None

    async def init_all_audioutils(self) -> None:
        """Instantiate all declared audio utils in parallel (async)."""
        async with self._init_lock:
            coro = [self._instantiate_audioutil(n) for n in list(self._audioutil_classes.keys())]
            await asyncio.gather(*coro)

    # ---------------- factories (DI) ----------------
    async def create_task(self, name: str, *, batch: Any = None, **kwargs: Any) -> Any:
        """
        Instantiate a task with positional audio util injections followed by keyword args.
        Returns an instance ready to start.
        """
        cls = self._task_classes.get(name.lower())
        if not cls:
            raise ValueError(f"Task '{name}' not registered")

        # ensure audio utils ready
        requires: Sequence[str] = getattr(cls, "depends", [])
        audio_args: List[Any] = []
        for dep in requires:
            inst = self._audioutil_instances.get(dep.lower())
            if inst is None:
                inst = await self._instantiate_audioutil(dep.lower())
            if inst is None:
                logger.warning(f"Task '{name}': missing audioutil dependency '{dep}'")
            audio_args.append(inst)

        # Build kwargs for ctor
        ctor_kwargs = dict(batch=batch, **kwargs)
        # Instantiate: alphapositional injection of audio utils then kwargs
        try:
            instance = cls(*audio_args, **ctor_kwargs)
        except TypeError:
            # fallback: try to instantiate without args (for tasks expecting later injection)
            instance = cls(**ctor_kwargs)
            # allow post-injection
            for i, dep_name in enumerate(requires):
                setter = getattr(instance, f"set_{dep_name}", None)
                if callable(setter):
                    setter(audio_args[i])
        # attach registry reference for potential later use
        setattr(instance, "_registry", self)
        return instance

    async def create_processor(
        self,
        name: str,
        *,
        config: Optional[Config] = None,
        **kwargs: Any,
    ) -> Any:
        cls = self._processor_classes.get(name.lower())
        if not cls:
            raise ValueError(f"Processor '{name}' not registered")

        requires: Sequence[str] = getattr(cls, "depends", [])
        util_args: List[Any] = []
        for dep in requires:
            inst = self._audioutil_instances.get(dep.lower())
            if inst is None:
                inst = await self._instantiate_audioutil(dep.lower())
            util_args.append(inst)

        ctor_kwargs = dict(config=(config or Config.get_sync()), **kwargs)
        instance = cls(*util_args, **ctor_kwargs)
        setattr(instance, "_registry", self)
        return instance

    # ---------------- getters ----------------
    def get_audioutil(self, name: str) -> Optional[Any]:
        return self._audioutil_instances.get(name.lower())

    def get_task_class(self, name: str) -> Optional[Type[Any]]:
        return self._task_classes.get(name.lower())

    def list_registered(self) -> dict:
        return {
            "audioutils": list(self._audioutil_classes.keys()),
            "tasks": list(self._task_classes.keys()),
            "processors": list(self._processor_classes.keys()),
            "stages": {k: v for k, v in self._stage_records.items()},
        }

    def tasks_for_stage(self, stage_type: StageType) -> List[str]:
        return list(self._stage_records.get(stage_type, []))

    def get_processor_class(self, name: str) -> Optional[Type[Any]]:
        return self._processor_classes.get(name.lower())

    def processor_names(self) -> List[str]:
        return list(self._processor_classes.keys())


# single global registry instance
registry = PluginRegistry()


class StageRegistry:
    def __init__(self) -> None:
        self._stages: Dict[StageType, List[Stage]] = {}

    def register_stage(self, stage: Stage) -> None:
        self._stages.setdefault(stage.stage_type, []).append(stage)

    def get_stages(self, stage_type: StageType) -> List[Stage]:
        return list(self._stages.get(stage_type, []))

    def all(self) -> List[Stage]:
        stages: List[Stage] = []
        for items in self._stages.values():
            stages.extend(items)
        return stages

    def find_stage(self, stage_name: str) -> Optional[Stage]:
        for stage in self.all():
            if stage.name == stage_name:
                return stage
        return None


stage_registry = StageRegistry()
