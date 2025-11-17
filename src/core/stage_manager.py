# src/core/stage_manager.py
from typing import Optional
from ..singletons import Logger
from .registry import stage_registry
from .stage import Stage
from .enums import StageType

logger = Logger()


class StageManager:
    """
    Lightweight manager used by tasks/plugins to register stages and check registry state.
    This class does not perform database writes; use StageTracker for persistence.
    """

    def register_stage(self, stage: Stage):
        """
        Register a Stage object (task-side). Plugins call this on import.
        """
        stage_registry.register_stage(stage)
        logger.info(f"StageManager: registered stage '{stage.name}' -> {stage.stage_type.name}")

    def register_stage_by_params(
        self,
        name: str,
        stage_type: StageType,
        task_name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """
        Convenience: register a stage by parameters (used by plugins that want a lighter syntax).
        """
        stage = Stage(name=name, stage_type=stage_type, task_name=task_name, description=description)
        self.register_stage(stage)

    def list_stages(self, stage_type: Optional[StageType] = None):
        """List stages for a StageType or all registered stages."""
        if stage_type:
            return stage_registry.get_stages(stage_type)
        return stage_registry.all()

    def get_stage(self, stage_name: str) -> Optional[Stage]:
        return stage_registry.find_stage(stage_name)
