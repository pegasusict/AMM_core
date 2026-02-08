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


from typing import Optional


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class EnvConfig:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///amm.db")
    DEBUG: bool = _as_bool(os.getenv("DEBUG", "false"), False)

    ICECAST_HOST: str = os.getenv("ICECAST_HOST", "localhost")
    ICECAST_PORT: int = int(os.getenv("ICECAST_PORT", "8000"))
    ICECAST_MOUNT_TEMPLATE: str = os.getenv("ICECAST_MOUNT_TEMPLATE", "/stream/{username}")


env_config = EnvConfig()
