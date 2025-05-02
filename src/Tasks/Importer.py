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
from amm.singletons.Stack import Stack
# scans files to be imported or deleted

def run_fast_scan_dir(stack: Stack, base_path: str, ext: list = (), clean: bool = False):
    """
    Parses directory (tree) and returns usable files according to extension filter and
    optionally removes any files not included in the filter

    TODO: what happens if file list exceeds physical capabilities?

    :param stack:       object      Stack Object to store
    :param base_path:   string      Base path to start scan from
    :param ext: list:   [ string, ] List of extension to report and retain
    :param clean:       bool        Remove any files whose extension is not listed in ext
                                    !!! USE WITH CARE !!!
    :return:
    """
    folders, files = [], []

    for file in os.scandir(base_path):
        if file.is_dir(follow_symlinks=False):
            folders.append(file.path)
            stack.add_counter('all_folders', 1 )
        elif file.is_file(follow_symlinks=False):
            if ext.__len__() < 1 or os.path.splitext(file.name)[1].lower() in ext:
                files.append(file.path)
                stack.add_counter('all_files', 1)
            elif clean and os.path.splitext(file.name)[1].lower() not in ext:
                os.remove(file)
                stack.add_counter('removed_files', 1)
    stack.add_counter('scanned_folders', 1)
    for path in list(folders):
        run_fast_scan_dir(stack, path, ext, clean)

    return folders, files