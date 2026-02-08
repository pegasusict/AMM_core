from __future__ import annotations

import sys
from pathlib import Path

TESTS_PATH = Path(__file__).resolve().parent
SRC_PATH = Path(__file__).resolve().parents[1] / "src"

while str(TESTS_PATH) in sys.path:
    sys.path.remove(str(TESTS_PATH))
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# Ensure the real src/Singletons wins over tests/Singletons.
mod = sys.modules.get("Singletons")
if mod is not None:
    mod_path = getattr(mod, "__file__", "") or ""
    if "tests/Singletons" in mod_path:
        sys.modules.pop("Singletons", None)
        for key in list(sys.modules.keys()):
            if key.startswith("Singletons."):
                sys.modules.pop(key, None)
