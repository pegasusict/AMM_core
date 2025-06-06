# -*- coding: utf-8 -*-
#  Copyleft 2021-2024 Mattijs Snepvangers.
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

from pathlib import Path
from typing import List

from Singletons.stack import Stack
from Singletons.logger import Logger
from Singletons.config import Config
from task import Task
from Enums import TaskType
from parser import Parser
from taskmanager import TaskManager


class Importer(Task):
    """
    Scans directories for files to import based on configured extensions.
    Optionally removes files not matching allowed extensions.
    """

    def __init__(self, config: Config):
        super().__init__(config=config, task_type=TaskType.IMPORTER)
        self.config = config
        self.logger = Logger(config)
        self.stack = Stack()
        self.files: List[Path] = []
        self.folders: List[Path] = []

        self.base_path = Path(self.config.get_path("import"))

        # Normalize extensions
        ext_val = self.config.get("extensions", "import")
        if isinstance(ext_val, str):
            self.ext = [ext_val.lower()]
        elif isinstance(ext_val, list):
            self.ext = [str(e).lower() for e in ext_val]
        else:
            self.ext = []

        self.clean = self.config.get("import", "clean", False)

        for counter in ("all_files", "all_folders", "removed_files", "scanned_folders", "scanned_files", "imported_files"):
            self.stack.add_counter(counter)

    def run(self):
        """Start the import task by scanning and invoking the parser."""
        if not self.base_path.exists():
            self.logger.error(f"Base path {self.base_path} does not exist.")
            return

        self._scan(self.base_path)

        if self.files:
            tm = TaskManager()
            tm.start_task(Parser, TaskType.PARSER, self.files)

    def _scan(self, path: Path):
        """Recursively scans path using pathlib."""
        self.stack.add_counter("scanned_folders")

        try:
            for entry in path.iterdir():
                if entry.is_dir():
                    self.folders.append(entry)
                    self.stack.add_counter("all_folders")
                    self._scan(entry)
                elif entry.is_file():
                    self._handle_file(entry)
        except Exception as e:
            self.logger.error(f"Error scanning {path}: {e}")

    def _handle_file(self, file_path: Path):
        """Handle a single file: include or optionally delete."""
        suffix = file_path.suffix.lower()
        if not self.ext or suffix in self.ext:
            self.files.append(file_path)
            self.stack.add_counter("all_files")
        elif self.clean:
            try:
                file_path.unlink(missing_ok=True)
                self.stack.add_counter("removed_files")
            except Exception as e:
                self.logger.warning(f"Failed to delete {file_path}: {e}")
