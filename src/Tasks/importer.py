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

import os
from pathlib import Path
from typing import List

from Singletons.stack import Stack
from Singletons.logger import Logger
from Singletons.config import Config
from task import Task, TaskType
from parser import Parser


class Importer(Task):
    """
    This class is used to import files from a directory.
    It scans the directory and returns a list of files to be imported.
    """
    files: List[Path] = []
    folders: List[Path] = []


    def __init__(self, config: Config):
        """
        Initializes the Importer class.

        Args:
            config: The configuration object.
        """
        super().__init__(config=config, task_type=TaskType.IMPORTER)
        self.config = config
        self.base_path = self.config.get("paths", "import")
        ext_val = self.config.get("extensions", "import")
        if isinstance(ext_val, list):
            self.ext = ext_val
        elif ext_val is None:
            self.ext = []
        else:
            self.ext = list(ext_val) if hasattr(ext_val, '__iter__') else [str(ext_val)] # type: ignore
        self.clean = self.config.get("import", "clean", False)
        self.stack = Stack()
        self.stack.add_counter('all_files', 0)
        self.stack.add_counter('all_folders', 0)
        self.stack.add_counter('removed_files', 0)
        self.stack.add_counter('scanned_folders', 0)
        self.stack.add_counter('scanned_files', 0)
        self.stack.add_counter('imported_files', 0)

    def run(self):
        """
        Parses directory (tree) and returns usable files according to extension filter and
        optionally removes any files not included in the filter."""
        self.fast_scan(self.base_path)
        # create task for files list to be processed by the parser
        # TODO: check how to hand this off to the TaskManager

        if self.files is not None and len(self.files) > 0:
            task = Parser(self.config, self.files)
            task.start()
            task.wait()


    def fast_scan(self, path):
        """
        Parses directory (tree) and returns usable files according to extension filter and
        optionally removes any files not included in the filter

        TODO: what happens if file list exceeds physical capabilities?

        Parameters:
        stack: (object)          Stack Object to store
        path:  (string)          Base path to start scan from
        ext:   (list:[string])   List of extension to import
        clean: (bool)            Remove any files whose extension is not listed in ext
                                        !!! USE WITH CARE !!!

        returns: folders: List[str], files: List[str]
        """

        if not os.path.exists(path):
            Logger(Config()).error(f"Base path {path} does not exist")
            return None, None

        for file in os.scandir(path):
            if file.is_dir(follow_symlinks=False):
                self.folders.append(Path(file.path))
                self.stack.add_counter('all_folders')
            elif file.is_file(follow_symlinks=False):
                if len(self.ext) < 1 or os.path.splitext(file.name)[1].lower() in self.ext:
                    self.files.append(Path(file.path))
                    self.stack.add_counter('all_files')
                elif self.clean:
                    os.remove(file)
                    self.stack.add_counter('removed_files')
        self.stack.add_counter('scanned_folders')
        for index, path in list(self.folders): # type: ignore
            self.folders.pop(index)
            self.fast_scan(path)

        return self.folders, self.files
