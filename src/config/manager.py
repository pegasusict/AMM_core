# manager.py

import asyncio
import logging
from pathlib import Path
from threading import Lock
from typing import Optional

from .models import AppConfig
from .defaults import DEFAULT_CONFIG
from .file_loader import read_config_file, write_config_file
from .env_loader import apply_environment
from .merger import merge_configs
from .watcher import watch_file
from .migrations import MIGRATIONS


logger = logging.getLogger("AMM.Config")


class AsyncConfigManager:
    _instance = None
    _instance_lock = Lock()

    @classmethod
    async def get(cls, config_file: Optional[Path] = None):
        """Async-safe singleton getter."""
        if cls._instance:
            return cls._instance

        loop = asyncio.get_running_loop()

        def create():
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls(config_file)
                return cls._instance

        return await loop.run_in_executor(None, create)

    # -----------------------------------------------------

    def __init__(self, config_file: Optional[Path]):
        self._async_lock = asyncio.Lock()
        self._thread_lock = Lock()

        self.config_file = Path(config_file) if config_file else Path("config.json")
        self._config: AppConfig = AppConfig(**DEFAULT_CONFIG)

        self.reload_sync()   # initial load
        self._watch_task = None

    # -----------------------------------------------------

def reload_sync(self):
    with self._thread_lock:
        file_cfg = read_config_file(self.config_file)

        # 1) merge defaults
        merged = merge_configs(DEFAULT_CONFIG, file_cfg)

        # 2) environment overrides
        merged = apply_environment(merged)

        # 3) apply migrations
        migrated = self._apply_migrations(merged)

        # 4) revalidate
        try:
            self._config = AppConfig(**migrated)
            logger.info("Configuration loaded successfully.")
        except Exception as e:
            logger.error(f"Config invalid: {e}")
            self._config = AppConfig(**DEFAULT_CONFIG)

        # 5) write back if migrations changed anything
        if migrated != file_cfg:
            write_config_file(self.config_file, migrated)
            logger.info("Config auto-updated due to migrations or missing defaults.")


    async def reload(self):
        """Async reload."""
        async with self._async_lock:
            await asyncio.to_thread(self.reload_sync)

    # -----------------------------------------------------
    # Saving
    # -----------------------------------------------------

    def save_sync(self):
        """
        Synchronously write the current config to disk.
        Thread-safe.
        """
        with self._thread_lock:
            data = self._config.model_dump(by_alias=True)
            write_config_file(self.config_file, data)
            logger.info("Configuration saved to disk.")

    async def save(self):
        """
        Async wrapper for saving.
        """
        async with self._async_lock:
            await asyncio.to_thread(self.save_sync)

    # -----------------------------------------------------
    # Apply changes & save
    # -----------------------------------------------------

    async def update(self, section: str, key: str, value):
        """
        Update a specific config field and save.
        Fully async and thread-safe.
        """
        async with self._async_lock:
            # update the in-memory model
            data = self._config.model_dump(by_alias=True)
            if section not in data:
                data[section] = {}

            data[section][key] = value

            # validate
            new_cfg = AppConfig(**data)
            self._config = new_cfg

            # save to disk
            await asyncio.to_thread(write_config_file, self.config_file, data)

            logger.info(f"Config updated: {section}.{key} = {value}")

    # -----------------------------------------------------
    # Reset to defaults
    # -----------------------------------------------------

    async def save_defaults(self):
        """
        Replace config with defaults and save.
        """
        async with self._async_lock:
            self._config = AppConfig(**DEFAULT_CONFIG)
            data = self._config.model_dump(by_alias=True)
            await asyncio.to_thread(write_config_file, self.config_file, data)
            logger.info("Configuration reset to defaults and saved.")

    # -----------------------------------------------------

    async def start_watching(self):
        if self._watch_task:
            return

        self._watch_task = asyncio.create_task(
            watch_file(self.config_file, self.reload)
        )

    # -----------------------------------------------------

    @property
    def model(self) -> AppConfig:
        return self._config

    def get_path(self, key: str) -> Path:
        base = Path(self._config.paths.base)
        return base if key == "base" else base / getattr(self._config.paths, key)


    def _apply_migrations(self, cfg: dict) -> dict:
        """
        Applies all migrations until config version reaches LATEST_VERSION.
        """
        version = str(cfg.get("version", "1.0"))

        while version in MIGRATIONS:
            logger.info(f"Applying migration for version {version} → next version...")
            migrate_fn = MIGRATIONS[version]
            cfg = migrate_fn(cfg)
            # bump version
            version = MIGRATIONS[version].__name__.split("_to_")[-1].replace("_", ".")
            cfg["version"] = version

        return cfg

