# env_loader.py

from __future__ import annotations

import os
from typing import Any, Dict

try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()  # executed on import if available


def apply_environment(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace ${VAR} with environment vars.
    """

    def resolve(value: Any) -> Any:
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            key = value[2:-1]
            return os.getenv(key, value)
        return value

    def walk(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: walk(resolve(v)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [walk(v) for v in obj]
        return resolve(obj)

    return walk(cfg)
