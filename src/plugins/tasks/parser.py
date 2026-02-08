# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
#  Part of AMM — GPLv3+.

"""Media Parser Task — extracts metadata using injected audioutil."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.task_base import TaskBase, register_task
from core.types import DBInterface, MediaParseProtocol
from core.enums import TaskType, StageType, PluginType
from Singletons import Logger, DBInstance
from dbmodels import DBFile
from core.exceptions import DatabaseError


def set_fields(from_: dict | object, to: dict | object) -> dict | object:
    """
    Copies all fields from `from_` to `to`. Supports both dicts and objects.
    Skips private attributes and callables.
    """

    def is_valid(key: str, value: Any) -> bool:
        return not key.startswith("_") and not callable(value)

    # Determine source fields
    if isinstance(from_, dict):
        source_items = from_.items()
    else:
        source_items = (
            (k, getattr(from_, k))
            for k in dir(from_)
            if hasattr(from_, k)
        )

    for key, value in source_items:
        if not is_valid(key, value):
            continue

        if isinstance(to, dict):
            to[key] = value
        else:
            setattr(to, key, value)

    return to


@register_task
class Parser(TaskBase):
    """
    Parses media files, extracts technical + metadata, and updates DBFile entries.

    Uses injected audioutil:
      - media_parse
    """

    name = "parser"
    description = "Parses media files and extracts metadata."
    version = "2.0.0"
    author = "Mattijs Snepvangers"
    plugin_type = PluginType.TASK

    task_type = TaskType.PARSER
    stage_type = StageType.IMPORT
    stage_name = "import"

    depends = ["media_parse"]

    exclusive = True          # Metadata writes should not overlap
    heavy_io = False          # Mutagen parsing is lightweight; change to True if needed

    def __init__(
        self,
        *,
        batch: dict[int, str | Path],
        media_parse: MediaParseProtocol,
    ) -> None:
        super().__init__()

        self.batch = {int(k): Path(v) for k, v in batch.items()}
        self.media_parse = media_parse
        self.logger = Logger()
        self.db: DBInterface = DBInstance

    # ------------------------------------------------------------------
    async def run(self) -> None:
        async for session in self.db.get_session():
            for file_id, file_path in self.batch.items():

                try:
                    # Parse metadata (injected util handles heavy lifting)
                    metadata = await self.media_parse(Path(file_path))

                    # Load DBFile
                    db_file = await session.get_one(DBFile, DBFile.id == file_id)
                    if db_file is None:
                        raise DatabaseError(f"DBFile {file_id} not found")

                    # Apply metadata to model
                    set_fields(metadata, db_file)

                    # Update stage
                    self.update_file_stage(file_id, session)

                    session.add(db_file)
                    self.logger.debug(f"Parsed file {file_path}")

                except Exception as e:
                    self.logger.error(f"Parser: Error processing {file_path}: {e}")
                    continue

                self.set_progress()

            await session.commit()
            await session.close()
