"""
Compatibility shim.

This module re-exports all models from `core.dbmodels` to keep legacy imports
working while the codebase standardizes on the core models.
"""

from __future__ import annotations

from core.dbmodels import *  # noqa: F403
import core.dbmodels as _core_dbmodels

__all__ = [name for name in dir(_core_dbmodels) if not name.startswith("_")]
