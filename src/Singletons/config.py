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
from typing import Optional, List, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pydantic import BaseModel, ValidationError

ENCODING = "utf-8"

# -----------------------------------
# Pydantic Models for Schema Validation
# -----------------------------------


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "amm.log"


class PathsConfig(BaseModel):
    base: str
    import_: str = "import/"
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
    import_: List[str]
    export: List[str]


class AppConfig(BaseModel):
    general: GeneralConfig
    musicbrainz: MusicBrainzConfig
    logging: LoggingConfig
    paths: PathsConfig
    extensions: ExtensionsConfig


# -----------------------------------
# Defaults
# -----------------------------------

DEFAULT_CONFIG = {
    "general": {"clean": True},
    "musicbrainz": {
        "host": "musicbrainz.org",
        "port": 443,
        "ignore_existing_acoustid_fingerprints": False,
    },
    "logging": {"level": "DEBUG", "file": "amm.log"},
    "paths": {
        "base": "/alpha/music/amm/",
        "import_": "import/",
        "process": "process/",
        "export": "export/",
        "music": "music/",
        "art": "art/",
    },
    "extensions": {
        "import_": [
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
# Temporary Logger Setup
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
# Config Class
# -----------------------------------


class Config:
    """Configuration Management Class (Auto-reloads, Pydantic validated)"""

    def __init__(self, config_file=None):
        self.main_path = Path(sys.modules["__main__"].__file__).resolve()  # type: ignore
        self.config_file = config_file or Path(self.main_path).parent / "config.json"
        self.config: AppConfig = self.load_config()
        self._observer = self._start_watching()

    def load_config(self) -> AppConfig:
        """Load and validate configuration from file."""
        if Path.exists(self.config_file):
            try:
                with Path.open(self.config_file, "r", encoding=ENCODING) as f:
                    file_config = json.load(f)
                    merged = self.merge_configs(DEFAULT_CONFIG, file_config)
                    validated = AppConfig(**merged)
                    temp_logger.info("Configuration loaded and validated.")
                    return validated
            except ValidationError as e:
                temp_logger.error(f"Config validation error: {e}")
                return AppConfig(**DEFAULT_CONFIG)
        else:
            temp_logger.warning("Config file not found, using default config.")
            self.save_config(DEFAULT_CONFIG)
            return AppConfig(**DEFAULT_CONFIG)

    def save_config(self, data: Optional[Dict] = None):
        """Save config to file (optional new data)."""
        to_save = data or self.config.dict()
        with Path.open(self.config_file, "w", encoding=ENCODING) as f:
            json.dump(to_save, f, indent=4)
        temp_logger.info("Config file saved.")

    def merge_configs(self, default: dict, override: dict) -> dict:
        """Recursively merge override config into default config."""
        result = copy.deepcopy(default)
        for key, value in override.items():
            if isinstance(value, dict) and key in result:
                result[key] = self.merge_configs(result.get(key, {}), value)
            else:
                result[key] = value
        return result

    def _start_watching(self):
        """Start Watchdog observer for auto-reloading config file."""
        observer = Observer()
        handler = ConfigFileEventHandler(self)
        observer.schedule(handler, str(self.config_file.parent), recursive=False)
        observer.start()
        temp_logger.info("Started config file watcher.")
        return observer

    def stop_watching(self):
        """Stop Watchdog observer when app shuts down."""
        self._observer.stop()
        self._observer.join()

    def use_real_logger(self, real_logger: logging.Logger):
        """Optionally switch to main Logger when it's ready."""
        global temp_logger
        temp_logger = real_logger
        temp_logger.info("Switched to main Logger.")
