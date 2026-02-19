#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    command.upgrade(config, "head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

