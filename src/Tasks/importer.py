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
from ..Singletons.stack import Stack
from ..Singletons.logger import Logger
from ..Singletons.database import DB
from ..Singletons.config import Config
from .task import Task, TaskType, TaskStatus

class Importer(Task):
    """
    This class is used to import files from a directory.
    It scans the directory and returns a list of files to be imported.
    """
    def __init__(self, config: Config, task_name="Importer", task_type=TaskType.IMPORTER):
        """
        Initializes the Importer class.

        Args:
            config: The configuration object.
        """
        super().__init__(config, task_name=task_name, task_type=task_type)
        self.config = config
        self.base_path = self.config.get("paths", "import")
        self.ext = self.config.get("extensions", "import")
        self.clean = self.config.get("clean", False)
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
        files, _ = self.fast_scan(self.base_path)
        # create task for files list to be processed by the parser
        if len(files) > 0:
            task = Parser(self.config, files)
            task.start()
            task.wait()

    def fast_scan(self, path):
        """
        Parses directory (tree) and returns usable files according to extension filter and
        optionally removes any files not included in the filter

        TODO: what happens if file list exceeds physical capabilities?

        :param stack:       object      Stack Object to store
        :param path:   string      Base path to start scan from
        :param ext: list:   [ string, ] List of extension to import
        :param clean:       bool        Remove any files whose extension is not listed in ext
                                        !!! USE WITH CARE !!!
        :return:
        """
        folders, files = [], []

        stack = self.stack
        ext = self.ext
        clean = self.clean

        if not os.path.exists(path):
            Logger.error(f"Base path {path} does not exist")
            return None, None

        for file in os.scandir(path):
            if file.is_dir(follow_symlinks=False):
                folders.append(file.path)
                stack.add_counter('all_folders')
            elif file.is_file(follow_symlinks=False):
                if ext.len < 1 or os.path.splitext(file.name)[1].lower() in ext:
                    files.append(file.path)
                    stack.add_counter('all_files')
                elif clean and os.path.splitext(file.name)[1].lower() not in ext:
                    os.remove(file)
                    stack.add_counter('removed_files')
        stack.add_counter('scanned_folders')
        for path in list(folders):
            folders2,files2 = self.fast_scan(path)
            if folders2:
                folders.extend(folders2)
            if files2:
                files.extend(files2)

        return folders, files

