# file_loader.py

import tomllib       # Python 3.11+ built-in TOML reader
try:
    import tomli_w  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    tomli_w = None
from pathlib import Path
import logging
from typing import Dict, Any
import json

ENCODING = "utf-8"
logger = logging.getLogger("AMM.Config")


def read_config_file(path: Path) -> Dict[str, Any]:
    if not path.exists():
        logger.warning(f"Config file missing: {path}")
        return {}

    try:
        if path.suffix.lower() == ".json":
            with path.open("r", encoding=ENCODING) as f:
                return json.load(f)
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.error(f"Cannot read config file: {e}")
        return {}


def write_config_file(path: Path, cfg: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if path.suffix.lower() == ".json":
            with path.open("w", encoding=ENCODING) as f:
                json.dump(cfg, f, indent=4)
            return
        if tomli_w is None:
            raise RuntimeError("tomli_w is required to write TOML config files.")
        with path.open("wb") as f:
            tomli_w.dump(cfg, f)
    except Exception as e:
        logger.error(f"Cannot write config file: {e}")
