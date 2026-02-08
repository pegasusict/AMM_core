from __future__ import annotations

from typing import Any, Optional

from .registry import registry


async def instantiate_task(task_name: str, *, batch: Any = None, **kwargs: Any) -> Any:
    """Instantiate a task by name using the central registry."""
    return await registry.create_task(task_name, batch=batch, **kwargs)


async def instantiate_processor(
    processor_name: str,
    *,
    config: Optional[Any] = None,
    **kwargs: Any,
) -> Any:
    """Instantiate a processor by name using the central registry."""
    return await registry.create_processor(processor_name, config=config, **kwargs)
