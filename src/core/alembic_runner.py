from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def run_alembic_upgrade(database_url: str | None = None) -> None:
    """Run `alembic upgrade head` using repo-local configuration."""
    root = Path(__file__).resolve().parents[2]
    alembic_ini = root / "alembic.ini"

    config = Config(str(alembic_ini))
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

