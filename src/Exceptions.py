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

class AMMError(Exception):
    """Base exception for AMM errors."""
    pass

class FileNotFoundError(AMMError):
    """Raised when a required file is not found."""
    pass

class FileError(AMMError):
    """Raised when there is something wrong with a required file."""
    pass

class InvalidConfigurationError(AMMError):
    """Raised when the configuration is invalid."""
    pass

class DatabaseConnectionError(AMMError):
    """Raised when the database connection fails."""
    pass

class PermissionDeniedError(AMMError):
    """Raised when an operation is not permitted."""
    pass

class OperationFailedError(AMMError):
    """Raised when a generic operation fails."""
    pass