# -*- coding: utf-8 -*-
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

from .task import Task
from .taskmanager import TaskManager
from .importer import Importer
from .parser import Parser
from .fingerprinter import FingerPrinter
from .deduper import Deduper
from .converter import Converter
from .exporter import Exporter
from .normalizer import Normalizer
from .sorter import Sorter
from .tagger import Tagger
from .trimmer import Trimmer
from .art_getter import ArtGetter
from .lyrics_getter import LyricsGetter
from .albumart_checker import AlbumArt_Checker
from .duplicate_checker import DuplicateChecker

__all__ = (
    "Task",
    "TaskManager",
    "Importer",
    "Parser",
    "FingerPrinter",
    "Deduper",
    "Converter",
    "Exporter",
    "Normalizer",
    "Sorter",
    "Tagger",
    "Trimmer",
    "ArtGetter",
    "LyricsGetter",
    "AlbumArt_Checker",
    "DuplicateChecker",
)
