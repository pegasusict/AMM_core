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

"""Compatibility wrapper around the async config manager."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional, Awaitable

from config import Config as AsyncConfigManager
from config.models import AppConfig


class Config:
    """Sync wrapper for AsyncConfigManager, for legacy call sites."""

    def __init__(self, config_file: Optional[Path] = None) -> None:
        self._manager: AsyncConfigManager = AsyncConfigManager.get_sync(config_file)

    @property
    def model(self) -> AppConfig:
        return self._manager.model

    def get_path(self, key: str) -> str:
        return str(self._manager.get_path(key))

    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        if key is None:
            # Support "section.key" or a bare key lookup across sections.
            if "." in section:
                sect, k = section.split(".", 1)
                return self._manager.get_value(sect, k, default)
            data = self._manager.model.model_dump(by_alias=True)
            if section in data and not isinstance(data[section], dict):
                return data.get(section, default)
            for sect, values in data.items():
                if isinstance(values, dict) and section in values:
                    return values.get(section, default)
            return default
        return self._manager.get_value(section, key, default)

    def get_string(self, section: str, key: str, default: Optional[str] = None) -> str:
        return self._manager.get_string(section, key, default)

    def get_int(self, section: str, key: str, default: int = 0) -> int:
        return self._manager.get_int(section, key, default)

    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        return self._manager.get_bool(section, key, default)

    def get_list(self, section: str, key: str, default: Optional[list[Any]] = None) -> list[Any]:
        return self._manager.get_list(section, key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        self._run_async(self._manager.update(section, key, value))

    def use_real_logger(self, _logger: Any) -> None:
        """Compatibility no-op for legacy call sites."""
        return None

    def stop_watching(self) -> None:
        """Compatibility no-op for legacy call sites."""
        return None

    def _run_async(self, coro: Awaitable[None]) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(coro)
            return
        loop.create_task(coro)
