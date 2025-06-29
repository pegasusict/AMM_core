#  Copyleft 2021-2025 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  AMM is free software: you can redistribute it and/or modify  it under the terms of the
#   GNU General Public License as published by  the Free Software Foundation, either version 3
#   of the License or any later version.
#
#  AMM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with AMM.  If not, see <https://www.gnu.org/licenses/>.

"""Configuration Management Module"""

import json
import logging
from pathlib import Path
import sys
import copy
from typing import Any, Optional, List, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pydantic import BaseModel, ValidationError, Field
from typing import Type, TypeVar, Callable

from ..exceptions import InvalidValueError

ENCODING = "utf-8"

# -----------------------------------
# Pydantic Models
# -----------------------------------


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "amm.log"


class PathsConfig(BaseModel):
    base: str
    import_: str = Field(default="import/", alias="import")
    process: str = "process/"
    export: str = "export/"
    music: str = "music/"
    art: str = "art/"


class GeneralConfig(BaseModel):
    clean: bool = True


class MusicBrainzConfig(BaseModel):
    host: str
    port: int
    ignore_existing_acoustid_fingerprints: bool


class ExtensionsConfig(BaseModel):
    import_: List[str] = Field(alias="import")
    export: List[str]


class AppConfig(BaseModel):
    version: str
    general: GeneralConfig
    musicbrainz: MusicBrainzConfig
    logging: LoggingConfig
    paths: PathsConfig
    extensions: ExtensionsConfig


# -----------------------------------
# Defaults
# -----------------------------------

CONFIG_VERSION = "1.0"

DEFAULT_CONFIG = {
    "version": "1.0",
    "general": {"clean": True},
    "musicbrainz": {
        "host": "musicbrainz.org",
        "port": 443,
        "ignore_existing_acoustid_fingerprints": False,
    },
    "logging": {"level": "DEBUG", "file": "amm.log"},
    "paths": {
        "base": "/alpha/music/amm/",
        "import": "import/",
        "process": "process/",
        "export": "export/",
        "music": "music/",
        "art": "art/",
    },
    "extensions": {
        "import": [
            "mp3",
            "flac",
            "ogg",
            "wav",
            "m4a",
            "aac",
            "wma",
            "opus",
            "mp4",
            "mp2",
        ],
        "export": ["mp3", "flac"],
    },
}

# -----------------------------------
# Logger Bootstrap
# -----------------------------------


def setup_basic_logger(config: Dict) -> logging.Logger:
    logger = logging.getLogger("config_logger")
    if not logger.hasHandlers():
        log_level = config.get("logging", {}).get("level", "INFO").upper()
        log_file = config.get("logging", {}).get("file", "config.log")

        logger.setLevel(getattr(logging, log_level, logging.INFO))

        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(ch)

        fh = logging.FileHandler(log_file, encoding=ENCODING)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)

    return logger


temp_logger = setup_basic_logger(DEFAULT_CONFIG)

# -----------------------------------
# Auto-Reload Watchdog Handler
# -----------------------------------


class ConfigFileEventHandler(FileSystemEventHandler):
    def __init__(self, config_instance):
        self.config_instance = config_instance

    def on_modified(self, event):
        if event.src_path == str(self.config_instance.config_file):
            temp_logger.info("Detected config file change, reloading...")
            self.config_instance.load_config()


# -----------------------------------
# Config Manager
# -----------------------------------


class Config:
    """Application-wide configuration manager with auto-reload and validation."""

    def __init__(self, config_file=None):
        self.main_path = Path(sys.modules["__main__"].__file__).resolve()  # type: ignore
        self.config_file = config_file or Path(self.main_path).parent / "config.json"
        self.config: AppConfig = self.load_config()
        self._observer = self._start_watching()

    def load_config(self) -> AppConfig:
        """Load and validate configuration from file, fallback to defaults."""
        try:
            if Path.exists(self.config_file):
                with Path.open(self.config_file, "r", encoding=ENCODING) as f:
                    file_config = json.load(f)

                if unknown_keys := set(file_config.keys()) - set(DEFAULT_CONFIG.keys()):
                    temp_logger.warning(
                        f"Unknown top-level keys in config: {unknown_keys}"
                    )

                merged = self.merge_configs(DEFAULT_CONFIG, file_config)

                try:
                    validated = AppConfig(**merged)
                    temp_logger.info("Configuration loaded and validated.")
                    return validated
                except ValidationError as e:
                    temp_logger.error(
                        "Configuration is invalid. Falling back to default."
                    )
                    for err in e.errors():
                        temp_logger.error(f"{err['loc']}: {err['msg']}")
                    return AppConfig(**DEFAULT_CONFIG)

            else:
                temp_logger.warning("Config file not found. Using defaults.")
                self.save_config(DEFAULT_CONFIG)
                return AppConfig(**DEFAULT_CONFIG)

        except json.JSONDecodeError as e:
            temp_logger.error(f"Invalid JSON: {e}")
        except Exception as e:
            temp_logger.exception(f"Unexpected config load error: {e}")

        return AppConfig(**DEFAULT_CONFIG)

    def save_config(self, data: Optional[Dict] = None):
        """Save the current or specified config to file."""
        to_save = data or self.config.model_dump(by_alias=True)
        with Path.open(self.config_file, "w", encoding=ENCODING) as f:
            json.dump(to_save, f, indent=4)
        temp_logger.info("Configuration saved.")

    def merge_configs(self, default: dict, override: dict) -> dict:
        """Recursively merge override into default."""
        result = copy.deepcopy(default)
        for key, value in override.items():
            if isinstance(value, dict) and key in result:
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _start_watching(self):
        """Watch config.json for changes and reload on update."""
        observer = Observer()
        handler = ConfigFileEventHandler(self)
        observer.schedule(handler, str(self.config_file.parent), recursive=False)
        observer.start()
        temp_logger.info("Started config auto-reload watcher.")
        return observer

    def stop_watching(self):
        """Stop config watcher (call during shutdown)."""
        self._observer.stop()
        self._observer.join()

    def use_real_logger(self, real_logger):
        """Replace temporary logger with application's main logger."""
        global temp_logger
        temp_logger = real_logger
        temp_logger.info("Config switched to main Logger.")

    T = TypeVar("T")

    def _get_value(
        self,
        section: str,
        key: str,
        expected_type: Type[T],
        default: Optional[T] = None,
        coercer: Optional[Callable[[Any], T]] = None,
    ) -> Optional[T]:
        value = self.config.model_dump(by_alias=True).get(section, {}).get(key, default)

        # Try coercion first if provided
        if coercer:
            try:
                return coercer(value)
            except Exception:
                temp_logger.warning(
                    f"[Config] {section}.{key} could not coerce to {expected_type.__name__}"
                )
                return default

        # Validate type directly
        if isinstance(value, expected_type):
            return value

        temp_logger.warning(
            f"[Config] {section}.{key} expected {expected_type.__name__}, got {type(value).__name__}"
        )
        return default

    def set_value(self, section: str, key: str, value):
        current = self.config.dict(by_alias=True)
        if section not in current:
            current[section] = {}
        current[section][key] = value
        self.save_config(current)

    def get_path(self, key: str) -> Path:
        base = Path(self.get_string("paths", "base"))  # type: ignore
        if base is None:
            raise InvalidValueError("Config: base path is not set!")
        if key == "base":
            return base
        subdir = Path(self.get_string("paths", key))  # type: ignore
        if subdir is None:
            raise InvalidValueError(f"Config: {key} path is not set!")
        return base / subdir

    def get_string(
        self, section: str, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        return self._get_value(section, key, str, default)

    def get_bool(
        self, section: str, key: str, default: Optional[bool] = None
    ) -> Optional[bool]:
        def to_bool(v):
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.lower() in {"true", "1", "yes", "on"}
            if isinstance(v, (int, float)):
                return bool(v)
            raise ValueError()

        return self._get_value(section, key, bool, default, coercer=to_bool)

    def get_int(
        self, section: str, key: str, default: Optional[int] = None
    ) -> Optional[int]:
        return self._get_value(section, key, int, default, coercer=int)

    def get_list(
        self, section: str, key: str, default: Optional[List[str]] = None
    ) -> Optional[List[str]]:
        def to_str_list(v):
            if isinstance(v, list) and all(isinstance(i, str) for i in v):
                return v
            raise ValueError()

        return self._get_value(section, key, list, default, coercer=to_str_list)
