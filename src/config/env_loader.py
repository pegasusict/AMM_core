# env_loader.py

import os
from dotenv import load_dotenv
from typing import Any, Dict

load_dotenv()   # executed on import


def apply_environment(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace ${VAR} with environment vars.
    """

    def resolve(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            key = value[2:-1]
            return os.getenv(key, value)
        return value

    def walk(obj):
        if isinstance(obj, dict):
            return {k: walk(resolve(v)) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [walk(v) for v in obj]
        return resolve(obj)

    return walk(cfg)
