# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path
from typing import List

from ..core.task_base import TaskBase
from ..core.registry import register_task
from ..enums import Stage
from ..dbmodels import DBFile


@dataclass
class ImporterConfig:
    base_path: Path
    extensions: List[str]
    clean: bool
    dry_run: bool

    @classmethod
    def from_config(cls, config, dry_run: bool = False):
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
            base_path=base_path,
            extensions=extensions,
            clean=clean,
            dry_run=dry_run,
        )


@register_task("importer")
class Importer(TaskBase):
    """
    Scans directories for files to import based on configured extensions.
    """

    # dependency injection from unified registry
    depends: list[str] = ["directory_scanner"]

    def __init__(self, config, directory_scanner, logger, db, stack):
        super().__init__(config)

        self.scanner = directory_scanner
        self.logger = logger
        self.db = db
        self.stack = stack
        self.stage = Stage.IMPORTED

        self.config_data = ImporterConfig.from_config(
            config=self.config,
            dry_run=config.get_bool("import", "dry_run", False),
        )

        for counter in (
            "all_files",
            "all_folders",
            "removed_files",
            "scanned_folders",
            "scanned_files",
            "imported_files",
        ):
            self.stack.add_counter(counter)

    async def run(self):
        base = self.config_data.base_path

        if not base.exists():
            self.logger.error(f"Import base path does not exist: {base}")
            return

        files, folders = await self.scanner.scan(base)

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
        else:
            self.logger.info(
                f"[Dry-run] Found {len(files_to_import)} files. No changes made."
            )

    def _should_import(self, file_path: Path) -> bool:
        suffix = file_path.suffix.lower()
        return not self.config_data.extensions or suffix in self.config_data.extensions

    def _should_remove(self, file_path: Path) -> bool:
        return not self._should_import(file_path) and self.config_data.clean

    def _remove_file(self, file_path: Path) -> None:
        if self.config_data.dry_run:
            self.logger.info(f"[Dry-run] Would delete: {file_path}")
            return

        try:
            file_path.unlink(missing_ok=True)
            self.stack.add_counter("removed_files")
        except Exception as e:
            self.logger.warning(f"Could not delete {file_path}: {e}")

    async def _import_files(self, files_to_import: List[Path]):
        process_path = Path(self.config.get_path("process"))
        process_path.mkdir(parents=True, exist_ok=True)

        async for session in self.db.get_session():
            for original_path in files_to_import:
                destination = self._unique_dest(process_path, original_path.name)

                try:
                    original_path.rename(destination)
                except Exception as e:
                    self.logger.error(
                        f"Failed to move {original_path} → {destination}: {e}"
                    )
                    continue

                db_file = DBFile(file_path=str(destination), stage=self.stage)
                session.add(db_file)
                self.stack.add_counter("imported_files")

            await session.commit()

        self.logger.info(
            f"Importer: {len(files_to_import)} files moved into {process_path}"
        )

    def _unique_dest(self, target_dir: Path, name: str) -> Path:
        base = target_dir / name
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
