from audioutil_manager import AudioUtilManager
from registry import task_registry, processor_registry


async def resolve_dependencies(audio_utils: list):
    resolved = []
    for name in audio_utils:
        instance = await AudioUtilManager.get(name)
        resolved.append(instance)
    return resolved


async def _instantiate_plugin(plugin_name: str, registry):
    """Instantiate a Task or Processor by name with dependencies resolved."""
    info = registry._registry.get(plugin_name)
    if not info:
        raise ValueError(f"Plugin '{plugin_name}' not found")

    cls = info["class"]
    deps = await resolve_dependencies(info["audio_utils"])
    return cls(*deps)

async def instantiate_task(task_name: str):
    return await _instantiate_plugin(task_name, task_registry)

async def instantiate_processor(processor_name: str):
    return await _instantiate_plugin(processor_name, processor_registry)
