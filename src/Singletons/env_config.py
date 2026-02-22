# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
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

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    load_dotenv = None

from typing import Optional

if load_dotenv is not None:
    load_dotenv()


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_csv(value: Optional[str], default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    items = tuple(part.strip() for part in value.split(",") if part.strip())
    return items or default


@dataclass(frozen=True)
class EnvConfig:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///amm.db")
    DEBUG: bool = _as_bool(os.getenv("DEBUG", "false"), False)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "").strip()
    ALLOW_INSECURE_DEFAULT_JWT_SECRET: bool = _as_bool(
        os.getenv("ALLOW_INSECURE_DEFAULT_JWT_SECRET", "false"),
        False,
    )

    TASK_RETENTION_ENABLED: bool = _as_bool(os.getenv("TASK_RETENTION_ENABLED", "true"), True)
    TASK_RETENTION_DAYS: int = int(os.getenv("TASK_RETENTION_DAYS", "30"))
    LOGIN_RATE_LIMIT_ENABLED: bool = _as_bool(os.getenv("LOGIN_RATE_LIMIT_ENABLED", "true"), True)
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = int(os.getenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "5"))
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "60"))
    REFRESH_RATE_LIMIT_ENABLED: bool = _as_bool(os.getenv("REFRESH_RATE_LIMIT_ENABLED", "true"), True)
    REFRESH_RATE_LIMIT_MAX_ATTEMPTS: int = int(os.getenv("REFRESH_RATE_LIMIT_MAX_ATTEMPTS", "20"))
    REFRESH_RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("REFRESH_RATE_LIMIT_WINDOW_SECONDS", "60"))
    GRAPHIQL_ENABLED: bool = _as_bool(os.getenv("GRAPHIQL_ENABLED", "false"), False)
    CORS_ALLOW_ALL: bool = _as_bool(os.getenv("CORS_ALLOW_ALL", "false"), False)
    CORS_ORIGINS: tuple[str, ...] = _as_csv(
        os.getenv("CORS_ORIGINS"),
        ("http://localhost", "http://localhost:8000", "http://127.0.0.1:8000"),
    )

    ICECAST_HOST: str = os.getenv("ICECAST_HOST", "localhost")
    ICECAST_PORT: int = int(os.getenv("ICECAST_PORT", "8000"))
    ICECAST_MOUNT_TEMPLATE: str = os.getenv("ICECAST_MOUNT_TEMPLATE", "/stream/{username}")


env_config = EnvConfig()
