# file_loader.py

import tomllib       # Python 3.11+ built-in TOML reader
import tomli_w       # Write support
from pathlib import Path
import logging
from typing import Dict, Any

ENCODING = "utf-8"
logger = logging.getLogger("AMM.Config")


def read_config_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        logger.warning(f"Config file missing: {path}")
        return {}

    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.error(f"Cannot read config file: {e}")
        return {}


def write_config_file(path: Path, cfg: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("wb") as f:
            tomli_w.dump(cfg, f)
    except Exception as e:
        logger.error(f"Cannot write config file: {e}")
