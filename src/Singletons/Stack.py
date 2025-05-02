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

"""Stats Stack
    A stack of stats for the AMM application.
    This is a singleton class that provides a global access point to the stats stack.
    It is used to keep track of various statistics related to the application.
"""

class Stack:
    """A stack of stats for the AMM application.
    This is a singleton class that provides a global access point to the stats stack.
    It is used to keep track of various statistics related to the application.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Stack, cls).__new__(cls)
            cls._instance._stats = {}
        return cls._instance

    def __init__(self):
        """Initialize the stack."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._stats = {}

    def add_counter(self, name: str, value: int = 1):
        """Add a counter to the stack."""
        if name not in self._stats:
            self._stats[name] = 0
        self._stats[name] += value
        return self._stats[name]

    def get_counter(self, name: str):
        """Get the value of a counter from the stack."""
        return self._stats.get(name, 0)

    def reset_counter(self, name: str):
        """Reset the value of a counter in the stack."""
        if name in self._stats:
            self._stats[name] = 0
        return self._stats[name]

    def reset_all(self):
        """Reset all counters in the stack."""
        for name in self._stats:
            self._stats[name] = 0
        return self._stats

    def get_all(self):
        """Get all counters from the stack."""
        return self._stats
