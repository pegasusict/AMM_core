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

from lib.SpecialTypes import ReadOnlyDict as RODict
from amm.singletons import DataBase as DBase


def has_state(file_id: int, state_id: int):
    """
    Checks if a particular state is present
    :param file_id: int     file ID
    :param state_id: int    State ID
    :return: bool
    """
    return state_id in has_states(file_id)


def has_states(file_id):
    """
    Gives list of set states for File_ID
    :param file_id: file ID
    :return: list
    """
    return DBase().get_list(get="states", table="files", where="file_id", equals=file_id)


instance = None


def check_socket():
    return True


class TaskManager:
    """
    :version: 0.0.0
    :author:  Mattijs Snepvangers pegasus.ict@gmail.com
    """

    # class singleton instance
    instance = None
    runningTasks = {}
    states: RODict[str, int] = {'imported': 0, 'fp': 1, 'mbid': 2, 'tags': 4, 'albumart': 8,
                                'lyrics': 16, 'trimmed': 32, 'normalized': 64}

    taskIDs: RODict[str, int] = {"importer": 100, "mbfp": 200, "dedup": 300, "mbq": 400,
                                 "art_get": 500, "lyrics_get": 600, "trimmer": 700,
                                 "normalizer": 800}

    def task_running(self, task_id):
        return self.runningTasks.__contains__(task_id)

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance
