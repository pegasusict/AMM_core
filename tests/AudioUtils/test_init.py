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

"""Test cases for AudioUtils module functions."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from AudioUtils import get_file_extension, get_file_type, FileTypes


class TestFileExtension:
    """Tests for the get_file_extension function."""

    @pytest.mark.parametrize(
        "file_path,expected_extension",
        [
            (Path("/path/to/file.mp3"), ".mp3"),
            (Path("/path/to/file.MP3"), ".mp3"),  # Test case insensitivity
            (Path("/path/to/file.flac"), ".flac"),
            (Path("/path/to/file.ogg"), ".ogg"),
            (Path("/path/to/file.m4a"), ".m4a"),
            (Path("/path/with.dots/file.wav"), ".wav"),
            (Path("/path/to/file"), ""),  # No extension
        ],
    )
    def test_get_file_extension(self, file_path, expected_extension):
        """Test the get_file_extension function returns correct extensions."""
        assert get_file_extension(file_path) == expected_extension


class TestFileType:
    """Tests for the get_file_type function."""

    @pytest.fixture
    def mock_logger_instance(self):
        """Create and return a mock logger instance."""
        return MagicMock()

    @pytest.fixture
    def mock_config(self):
        """Create and return a mock config instance."""
        return MagicMock()

    @pytest.mark.parametrize("file_type", [".mp3", ".mp4", ".flac", ".wav", ".ogg", ".ape", ".asf"])
    @patch("AudioUtils.Logger")
    @patch("AudioUtils.Config")
    def test_get_file_type_supported(self, mock_config_cls, mock_logger_cls, file_type):
        """Test get_file_type function with supported file types."""
        test_path = Path(f"/path/to/file{file_type}")

        # Create a patch for the FileTypes enum to simulate the file type being supported
        with patch("AudioUtils.get_file_extension", return_value=file_type):
            with patch("AudioUtils.FileTypes.__members__.__contains__", return_value=True):
                result = get_file_type(test_path)

                # Check that the function returns the file extension for supported types
                assert result == file_type

                # Ensure logger was not called for supported types
                mock_logger_cls.assert_not_called()

    @patch("AudioUtils.Logger")
    @patch("AudioUtils.Config")
    def test_get_file_type_unsupported(self, mock_config_cls, mock_logger_cls, mock_logger_instance):
        """Test get_file_type function with unsupported file types."""
        # Set up the mock logger
        mock_logger_cls.return_value = mock_logger_instance

        # Test with an unsupported file extension
        test_path = Path("/path/to/file.xyz")
        unsupported_extension = ".xyz"

        with patch("AudioUtils.get_file_extension", return_value=unsupported_extension):
            with patch("AudioUtils.FileTypes.__members__.__contains__", return_value=False):
                result = get_file_type(test_path)

                # Check that the function returns None for unsupported types
                assert result is None

                # Verify that the logger was called with the correct error message
                mock_logger_instance.error.assert_called_once_with(message=f"Unsupported file type: {unsupported_extension}")


class TestFileTypesEnum:
    """Tests for the FileTypes enum."""

    @pytest.mark.parametrize("file_type", ["MP3", "MP4", "FLAC", "WAV", "OGG", "APE", "ASF"])
    def test_file_types_enum_contains_expected_types(self, file_type):
        """Test that the FileTypes enum contains all expected file types."""
        assert file_type in [member.name for member in FileTypes]
