# audioutils/directory_scanner.py
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, ClassVar

from core.audioutil_base import AudioUtilBase, register_audioutil
from Singletons import Logger

logger = Logger()  # singleton logger


@register_audioutil
class DirectoryScanner(AudioUtilBase):
    """
    Recursively scans a directory and returns (files, folders).
    """

    # --- Required plugin metadata ---
    name: ClassVar[str] = "directory_scanner"
    description: ClassVar[str] = "Recursively scans directories and returns file and folder lists."
    version: ClassVar[str] = "1.0.0"
    author: ClassVar[str] = "Mattijs Snepvangers"
    exclusive: ClassVar[bool] = True
    heavy_io: ClassVar[bool] = False    # light I/O (metadata only)

    def __init__(self) -> None:
        self.logger = Logger()

    async def scan(self, path: Path) -> Tuple[List[Path], List[Path]]:
        """Return (files, folders) recursively under a given directory."""
        files: List[Path] = []
        folders: List[Path] = []

        try:
            for entry in path.iterdir():
                if entry.is_dir():
                    folders.append(entry)
                    sub_files, sub_folders = await self.scan(entry)
                    files.extend(sub_files)
                    folders.extend(sub_folders)
                elif entry.is_file():
                    files.append(entry)
        except Exception as e:
            self.logger.error(f"Error scanning {path}: {e}")
            raise RuntimeError(f"Error scanning {path}: {e}") from e

        return files, folders