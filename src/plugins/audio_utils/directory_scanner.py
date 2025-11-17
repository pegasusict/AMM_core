# -*- coding: utf-8 -*-
from pathlib import Path
from typing import List, Tuple

from ..core.audioutil_base import AudioUtilBase
from ..core.registry import register_audioutil


@register_audioutil("directory_scanner")
class DirectoryScanner(AudioUtilBase):
    """
    Recursively scans a directory and returns lists of files and folders.
    """

    depends: list[str] = []

    async def scan(self, path: Path) -> Tuple[List[Path], List[Path]]:
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
            raise RuntimeError(f"Error scanning {path}: {e}") from e

        return files, folders
