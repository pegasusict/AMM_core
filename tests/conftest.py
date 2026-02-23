from __future__ import annotations

import sys
from pathlib import Path

TESTS_PATH = Path(__file__).resolve().parent
SRC_PATH = Path(__file__).resolve().parents[1] / "src"

# Legacy import tests in tests/generated target removed module paths
# (GraphQL.* and Server.auth). Ignore them instead of adding runtime shims.
collect_ignore_glob = [
    "generated/test_GraphQL_*.py",
    "generated/test_Server_auth.py",
]

while str(TESTS_PATH) in sys.path:
    sys.path.remove(str(TESTS_PATH))
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
