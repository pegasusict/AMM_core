import asyncio
import importlib
import pkgutil
from pathlib import Path

from Singletons import Logger
from .registry import registry

logger = Logger()

PLUGIN_MODULES = [
    "amm.plugins.audio_utils",
    "amm.plugins.tasks",
    "amm.plugins.processors",
]

async def load_plugins_from_package(package_name: str) -> None:
    """Dynamically import all submodules in a package asynchronously."""
    package = importlib.import_module(package_name)
    package_path = Path(package.__file__).parent

    tasks = []
    for _, module_name, is_pkg in pkgutil.iter_modules([str(package_path)]):
        if is_pkg:
            continue
        full_name = f"{package_name}.{module_name}"
        logger.debug(f"Discovered plugin module: {full_name}")
        tasks.append(asyncio.to_thread(importlib.import_module, full_name))

    await asyncio.gather(*tasks)
    logger.info(f"All modules in '{package_name}' imported.")

async def bootstrap_plugins() -> None:
    """Load all plugins in the correct dependency order."""
    logger.info("🔧 Bootstrapping AMM plugin system...")

    # 1️⃣ AudioUtils first
    logger.info("→ Loading Audio Utilities...")
    await load_plugins_from_package("amm.plugins.audio_utils")
    logger.info(f"✔ Loaded {len(registry._audioutil_classes)} audio utilities.")

    # 2️⃣ Then Tasks
    logger.info("→ Loading Tasks...")
    await load_plugins_from_package("amm.plugins.tasks")
    logger.info(f"✔ Loaded {len(registry._task_classes)} tasks.")

    # 3️⃣ Finally Processors
    logger.info("→ Loading Processors...")
    await load_plugins_from_package("amm.plugins.processors")
    logger.info(f"✔ Loaded {len(registry._processor_classes)} processors.")

    logger.info("✅ Plugin system fully bootstrapped.")
