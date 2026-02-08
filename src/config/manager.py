# manager.py

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from threading import Lock
from typing import Any, ClassVar, Dict, Optional, TypeVar, cast

from .models import AppConfig
from .defaults import DEFAULT_CONFIG
from .file_loader import read_config_file, write_config_file
from .env_loader import apply_environment
from .merger import merge_configs
from .watcher import watch_file
from .migrations import MIGRATIONS


logger = logging.getLogger("AMM.Config")

T = TypeVar("T")


class AsyncConfigManager:
    _instance: ClassVar[Optional["AsyncConfigManager"]] = None
    _instance_lock: ClassVar[Lock] = Lock()

    @classmethod
    async def get(cls, config_file: Optional[Path] = None) -> "AsyncConfigManager":
        """Async-safe singleton getter."""
        if cls._instance is not None:
            return cls._instance

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: cls.get_sync(config_file))

    @classmethod
    def get_sync(cls, config_file: Optional[Path] = None) -> "AsyncConfigManager":
        """Sync-safe singleton getter (for non-async contexts)."""
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls(config_file)
            return cls._instance

    # -----------------------------------------------------

    def __init__(self, config_file: Optional[Path]) -> None:
        self._async_lock = asyncio.Lock()
        self._thread_lock = Lock()

        self.config_file = Path(config_file) if config_file else Path("config.json")
        self._config: AppConfig = AppConfig(**DEFAULT_CONFIG)

        self.reload_sync()   # initial load
        self._watch_task: Optional[asyncio.Task[Any]] = None

    # -----------------------------------------------------

    def reload_sync(self) -> None:
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

    async def reload(self) -> None:
        """Async reload."""
        async with self._async_lock:
            await asyncio.to_thread(self.reload_sync)

    # -----------------------------------------------------
    # Saving
    # -----------------------------------------------------

    def save_sync(self) -> None:
        """
        Synchronously write the current config to disk.
        Thread-safe.
        """
        with self._thread_lock:
            data = self._config.model_dump(by_alias=True)
            write_config_file(self.config_file, data)
            logger.info("Configuration saved to disk.")

    async def save(self) -> None:
        """Async wrapper for saving."""
        async with self._async_lock:
            await asyncio.to_thread(self.save_sync)

    # -----------------------------------------------------
    # Apply changes & save
    # -----------------------------------------------------

    async def update(self, section: str, key: str, value: Any) -> None:
        """
        Update a specific config field and save.
        Fully async and thread-safe.
        """
        async with self._async_lock:
            # update the in-memory model
            data = self._config.model_dump(by_alias=True)
            if section not in data:
                data[section] = {}

            if isinstance(data[section], dict):
                data[section][key] = value
            else:
                data[section] = {key: value}

            # validate
            new_cfg = AppConfig(**data)
            self._config = new_cfg

            # save to disk
            await asyncio.to_thread(write_config_file, self.config_file, data)

            logger.info(f"Config updated: {section}.{key} = {value}")

    # -----------------------------------------------------
    # Reset to defaults
    # -----------------------------------------------------

    async def save_defaults(self) -> None:
        """Replace config with defaults and save."""
        async with self._async_lock:
            self._config = AppConfig(**DEFAULT_CONFIG)
            data = self._config.model_dump(by_alias=True)
            await asyncio.to_thread(write_config_file, self.config_file, data)
            logger.info("Configuration reset to defaults and saved.")

    # -----------------------------------------------------

    async def start_watching(self) -> None:
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
        if key == "base":
            return base
        attr = "import_" if key == "import" else key
        return base / getattr(self._config.paths, attr)

    def get_value(self, section: str, key: str, default: Optional[T] = None) -> Optional[T]:
        data = self._config.model_dump(by_alias=True)
        section_value = data.get(section)
        if isinstance(section_value, dict):
            return cast(Optional[T], section_value.get(key, default))
        return default

    def get_string(self, section: str, key: str, default: Optional[str] = None) -> str:
        value = self.get_value(section, key, default)
        if value is None:
            return "" if default is None else default
        return str(value)

    def get_int(self, section: str, key: str, default: int = 0) -> int:
        value = self.get_value(section, key, default)
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default

    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        value = self.get_value(section, key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value) if value is not None else default

    def get_list(self, section: str, key: str, default: Optional[list[Any]] = None) -> list[Any]:
        value = self.get_value(section, key, default or [])
        if isinstance(value, list):
            return value
        if value is None:
            return default or []
        return [value]

    def _apply_migrations(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Applies all migrations until config version reaches LATEST_VERSION."""
        version = str(cfg.get("version", "1.0"))

        while version in MIGRATIONS:
            logger.info(f"Applying migration for version {version} → next version...")
            migrate_fn = MIGRATIONS[version]
            cfg = migrate_fn(cfg)
            # bump version
            version = MIGRATIONS[version].__name__.split("_to_")[-1].replace("_", ".")
            cfg["version"] = version

        return cfg
