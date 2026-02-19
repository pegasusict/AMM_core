import importlib
import pkgutil
from pathlib import Path

from Singletons import Logger
from .registry import registry

logger = Logger()

PLUGIN_MODULES = [
    "plugins.audio_utils",
    "plugins.tasks",
    "plugins.processors",
]

async def load_plugins_from_package(package_name: str) -> None:
    """Dynamically import all submodules in a package asynchronously."""
    package = importlib.import_module(package_name)
    package_paths = [str(Path(p)) for p in getattr(package, "__path__", [])]
    if not package_paths:
        raise ImportError(f"Package '{package_name}' has no importable __path__")

    for _, module_name, is_pkg in pkgutil.iter_modules(package_paths):
        if is_pkg:
            continue
        full_name = f"{package_name}.{module_name}"
        logger.debug(f"Discovered plugin module: {full_name}")
        try:
            importlib.import_module(full_name)
        except Exception as e:
            logger.error(f"Failed to import plugin module '{full_name}': {e}")
            continue

    logger.info(f"All modules in '{package_name}' imported.")

async def bootstrap_plugins() -> None:
    """Load all plugins in the correct dependency order."""
    logger.info("Bootstrapping AMM plugin system...")

    # 1) AudioUtils first
    logger.info("Loading audio utilities...")
    await load_plugins_from_package("plugins.audio_utils")
    logger.info(f"Loaded {len(registry._audioutil_classes)} audio utilities.")

    # 2) Then Tasks
    logger.info("Loading tasks...")
    await load_plugins_from_package("plugins.tasks")
    logger.info(f"Loaded {len(registry._task_classes)} tasks.")

    # 3) Finally Processors
    logger.info("Loading processors...")
    await load_plugins_from_package("plugins.processors")
    logger.info(f"Loaded {len(registry._processor_classes)} processors.")

    logger.info("Plugin system fully bootstrapped.")
