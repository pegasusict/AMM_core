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
from typing import List, Tuple
from dataclasses import dataclass

from ..Singletons import DB, DBInstance, Stack, Logger, Config
from ..dbmodels import DBFile
from .task import Task
from ..enums import Stage, TaskType


@dataclass
class ImporterConfig:
    base_path: Path
    extensions: List[str]
    clean: bool
    dry_run: bool

    @classmethod
    def from_config(cls, config: Config, dry_run: bool = False) -> "ImporterConfig":
        base_path = Path(config.get_path("import"))
        raw_ext = config.get_list("extensions", "import")
        if isinstance(raw_ext, str):
            extensions = [raw_ext.lower()]
        elif isinstance(raw_ext, list):
            extensions = [str(e).lower() for e in raw_ext]
        else:
            extensions = []

        clean = bool(config.get_bool("import", "clean", False))
        return cls(
            base_path=base_path, extensions=extensions, clean=clean, dry_run=dry_run
        )


class DirectoryScanner:
    def __init__(self, config: ImporterConfig) -> None:
        self.config: ImporterConfig = config

    def scan(self, path: Path) -> Tuple[List[Path], List[Path]]:
        """Recursively scan directories and return files and folders."""
        files: List[Path] = []
        folders: List[Path] = []

        try:
            for entry in path.iterdir():
                if entry.is_dir():
                    folders.append(entry)
                    sub_files, sub_folders = self.scan(entry)
                    files.extend(sub_files)
                    folders.extend(sub_folders)
                elif entry.is_file():
                    files.append(entry)
        except Exception as e:
            raise RuntimeError(f"Error scanning {path}: {e}") from e

        return files, folders


class Importer(Task):
    """
    Scans directories for files to import based on configured extensions.
    Optionally removes files not matching allowed extensions (unless in dry-run mode).
    """

    def __init__(self, config: Config, dry_run: bool = False) -> None:
        super().__init__(config=config, task_type=TaskType.IMPORTER)
        self.logger: Logger = Logger(config)
        self.stack: Stack = Stack()
        self.config_data: ImporterConfig = ImporterConfig.from_config(
            config, dry_run=dry_run
        )
        self.stage: Stage = Stage.IMPORTED
        self.db: DB = DBInstance

        for counter in (
            "all_files",
            "all_folders",
            "removed_files",
            "scanned_folders",
            "scanned_files",
            "imported_files",
        ):
            self.stack.add_counter(counter)

    async def run(self) -> None:
        if not self.config_data.base_path.exists():
            self.logger.error(f"Base path {self.config_data.base_path} does not exist.")
            return

        scanner: DirectoryScanner = DirectoryScanner(config=self.config_data)
        files, folders = scanner.scan(self.config_data.base_path)

        self.stack.add_counter("scanned_folders", len(folders))
        self.stack.add_counter("scanned_files", len(files))

        files_to_import: List[Path] = []

        for file_path in files:
            if self._should_import(file_path):
                files_to_import.append(file_path)
                self.stack.add_counter("all_files")
            elif self._should_remove(file_path):
                self._remove_file(file_path)

        if files_to_import and not self.config_data.dry_run:
            await self._import_files(files_to_import)
        elif self.config_data.dry_run:
            self.logger.info(
                f"[Dry-run] Found {len(files_to_import)} files. No changes made."
            )

    def _should_import(self, file_path: Path) -> bool:
        suffix: str = file_path.suffix.lower()
        return not self.config_data.extensions or suffix in self.config_data.extensions

    def _should_remove(self, file_path: Path) -> bool:
        return not self._should_import(file_path) and self.config_data.clean

    def _remove_file(self, file_path: Path) -> None:
        if self.config_data.dry_run:
            self.logger.info(f"[Dry-run] Would remove: {file_path}")
        else:
            try:
                file_path.unlink(missing_ok=True)
                self.stack.add_counter("removed_files")
            except Exception as e:
                self.logger.warning(f"Failed to delete {file_path}: {e}")

    async def _import_files(self, files_to_import: List[Path]) -> None:
        process_path = Path(self.config.get_path("process"))
        process_path.mkdir(parents=True, exist_ok=True)

        async for session in self.db.get_session():
            for original_path in files_to_import:
                destination_path = self._resolve_destination_path(
                    process_path, original_path.name
                )

                try:
                    if self.config_data.dry_run:
                        self.logger.info(
                            f"[Dry-run] Would move {original_path} → {destination_path}"
                        )
                    else:
                        original_path.rename(destination_path)
                except Exception as e:
                    self.logger.error(
                        f"Failed to move {original_path} to {destination_path}: {e}"
                    )
                    continue

                db_file = DBFile(file_path=str(destination_path), stage=self.stage)
                session.add(db_file)
                self.stack.add_counter("imported_files")

            await session.commit()
            await session.close()

        self.logger.info(f"Imported {len(files_to_import)} files to {process_path}")

    def _resolve_destination_path(self, target_dir: Path, file_name: str) -> Path:
        """
        Resolve a unique destination path in case of name conflicts.
        """
        base = target_dir / file_name
        if not base.exists():
            return base

        stem = base.stem
        suffix = base.suffix
        counter = 1

        while True:
            candidate = target_dir / f"{stem} ({counter}){suffix}"
            if not candidate.exists():
                return candidate
            counter += 1
