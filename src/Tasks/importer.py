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

"""This module implements the Importer task for scanning directories
and importing files based on configured extensions, with optional cleanup."""

from pathlib import Path
from typing import List, Type
from dataclasses import dataclass

from Singletons.stack import Stack
from Singletons.logger import Logger
from Singletons.config import Config
from task import Task
from Enums import TaskType


@dataclass
class ImporterConfig:
    base_path: Path
    extensions: List[str]
    clean: bool
    dry_run: bool

    @classmethod
    def from_config(cls, config, dry_run: bool = False) -> "ImporterConfig":
        base_path = Path(config.get_path("import"))
        raw_ext = config.get("extensions", "import")
        if isinstance(raw_ext, str):
            extensions = [raw_ext.lower()]
        elif isinstance(raw_ext, list):
            extensions = [str(e).lower() for e in raw_ext]
        else:
            extensions = []

        clean = config.get("import", "clean", False)
        return cls(
            base_path=base_path, extensions=extensions, clean=clean, dry_run=dry_run
        )


class DirectoryScanner:
    def __init__(self, config: ImporterConfig, logger, stack):
        self.config = config
        self.logger = logger
        self.stack = stack
        self.files: List[Path] = []
        self.folders: List[Path] = []

    def scan(self, path: Path):
        self.stack.add_counter("scanned_folders")
        try:
            for entry in path.iterdir():
                if entry.is_dir():
                    self.folders.append(entry)
                    self.stack.add_counter("all_folders")
                    self.scan(entry)
                elif entry.is_file():
                    self._handle_file(entry)
        except Exception as e:
            self.logger.error(f"Error scanning {path}: {e}")

    def _handle_file(self, file_path: Path):
        suffix = file_path.suffix.lower()
        if not self.config.extensions or suffix in self.config.extensions:
            self.files.append(file_path)
            self.stack.add_counter("all_files")
        elif self.config.clean:
            if self.config.dry_run:
                self.logger.info(f"[Dry-run] Would remove: {file_path}")
            else:
                try:
                    file_path.unlink(missing_ok=True)
                    self.stack.add_counter("removed_files")
                except Exception as e:
                    self.logger.warning(f"Failed to delete {file_path}: {e}")


class Importer(Task):
    """
    Scans directories for files to import based on configured extensions.
    Optionally removes files not matching allowed extensions (unless in dry-run mode).
    """

    def __init__(
        self,
        config: Config,
        task_manager_class: Type = None,  # type: ignore
        parser_class: Type = None,  # type: ignore
        dry_run: bool = False,
    ):
        super().__init__(config=config, task_type=TaskType.IMPORTER)
        self.logger = Logger(config)
        self.stack = Stack()
        self.config_data = ImporterConfig.from_config(config, dry_run=dry_run)

        for counter in (
            "all_files",
            "all_folders",
            "removed_files",
            "scanned_folders",
            "scanned_files",
            "imported_files",
        ):
            self.stack.add_counter(counter)

        # Dependency-injected components for testability
        from taskmanager import TaskManager
        from parser import Parser

        self.TaskManager = task_manager_class or TaskManager
        self.Parser = parser_class or Parser

    def run(self):
        if not self.config_data.base_path.exists():
            self.logger.error(f"Base path {self.config_data.base_path} does not exist.")
            return

        scanner = DirectoryScanner(
            config=self.config_data, logger=self.logger, stack=self.stack
        )
        scanner.scan(self.config_data.base_path)

        if scanner.files and not self.config_data.dry_run:
            tm = self.TaskManager()
            tm.start_task(self.Parser, TaskType.PARSER, scanner.files)
        elif self.config_data.dry_run:
            self.logger.info(
                f"[Dry-run] Found {len(scanner.files)} files for parsing. No changes made."
            )
