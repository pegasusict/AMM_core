#  Copyleft 2021-2025 Mattijs Snepvangers.
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

"""Parses media files and extracts metadata from them.
It uses the mutagen library to read and write metadata to media files.
"""

from pathlib import Path
from typing import Any

from ..exceptions import DatabaseError
from ..enums import Stage, TaskType
from ..dbmodels import DBFile
from .task import Task
from ..Singletons import Config, DBInstance, Logger
from ..AudioUtils.media_parser import MediaParser


def set_fields(from_: dict | object, to: dict | object) -> dict | object:
    """
    Copies all fields/attributes from `from_` to `to`.
    Supports both dicts and objects. Skips private and callables.
    """

    def is_valid(key: str, value: Any) -> bool:
        return not key.startswith("_") and not callable(value)

    # Extract source fields
    if isinstance(from_, dict):
        source_items = from_.items()
    else:
        source_items = ((k, getattr(from_, k)) for k in dir(from_) if hasattr(from_, k))

    for key, value in source_items:
        if not is_valid(key, value):
            continue

        if isinstance(to, dict):
            to[key] = value
        else:
            setattr(to, key, value)

    return to


class Parser(Task):
    """
    Parses media files in a batch, extracts metadata, and registers them in the database.
    """

    def __init__(self, config: Config, batch: dict[int, Path]):
        super().__init__(config=config, task_type=TaskType.PARSER)
        self.config = config
        self.batch = batch
        self.db = DBInstance
        self.logger = Logger(config)
        self.parser = MediaParser(config)
        self.stage = Stage.PARSED

    async def run(self) -> None:
        """
        Parses all files in the batch, extracts metadata, and registers them in the database.
        Skips files that are already imported.
        """
        async for session in self.db.get_session():
            for file_id, file_path in self.batch:  # type: ignore
                try:
                    metadata = self.parser.parse(Path(file_path))

                    db_file = session.get_one(DBFile, DBFile.id == file_id)
                    if db_file is None:
                        raise DatabaseError("DB did not return a valid file object.")

                    set_fields(metadata, db_file)  # type: ignore
                    db_file.stage = int(Stage(db_file.stage) | self.stage)  # type: ignore
                    session.add(db_file)
                    self.logger.debug(f"Parsed file {file_path}")

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path}: {e}")
                    continue

                self.set_progress()
            await session.commit()
            await session.close()
