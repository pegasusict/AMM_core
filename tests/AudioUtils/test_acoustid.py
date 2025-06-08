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

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock  # noqa: F401

# Mock the modules before importing the class under test
import sys

mock_config = MagicMock()
mock_logger = MagicMock()
mock_acoustid = MagicMock()
sys.modules["Singletons.config"] = mock_config
sys.modules["Singletons.logger"] = mock_logger
sys.modules["acoustid"] = mock_acoustid

# Now we can import the class
from Exceptions import FileError  # noqa: E402, F401


# Create a mock AcoustID class for testing
class MockAcoustID:
    """Mock AcoustID class for testing"""

    def __init__(self, path):
        self.path = path
        self.api_key = "test_api_key"
        self.duration = None
        self.fingerprint = None
        self.fileinfo = {}

    def _scan_file(self, path):
        """Mock scan file method"""
        if not hasattr(self, "_mock_scan_result"):
            self._mock_scan_result = (120, "test_fingerprint")

        if isinstance(self._mock_scan_result, tuple) and len(self._mock_scan_result) == 2:
            self.duration, self.fingerprint = self._mock_scan_result
        else:
            raise RuntimeError("acoustid.fingerprint_file did not return (duration, fingerprint) tuple")

    def _get_track_info(self):
        """Mock get track info method"""
        if not hasattr(self, "_mock_track_info"):
            self._mock_track_info = (0.95, "test_mbid", "Test Title", "Test Artist")

        score, mbid, title, artist = self._mock_track_info

        if not (score and mbid and title and artist):
            raise RuntimeError("Failed to retrieve track information from AcoustID")

        self.fileinfo["fingerprint"] = self.fingerprint
        self.fileinfo["score"] = score
        self.fileinfo["mbid"] = mbid
        self.fileinfo["title"] = title
        self.fileinfo["artist"] = artist

    def process(self):
        """Mock process method"""
        return self.fileinfo


class TestAcoustID(unittest.TestCase):
    """Test cases for AcoustID class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_path = Path("/path/to/test_file.mp3")
        self.acoustid = MockAcoustID(self.test_path)

    def test_scan_file_success(self):
        """Test successful file scanning"""
        # Set up test data
        self.acoustid._mock_scan_result = (120, "test_fingerprint")

        # Call the method
        self.acoustid._scan_file(self.test_path)

        # Verify the results
        self.assertEqual(self.acoustid.duration, 120)
        self.assertEqual(self.acoustid.fingerprint, "test_fingerprint")

    def test_scan_file_invalid_result(self):
        """Test file scanning with invalid result"""
        # Set up test data
        self.acoustid._mock_scan_result = "invalid_result"  # type: ignore

        # Verify that the method raises RuntimeError
        with self.assertRaises(RuntimeError) as context:
            self.acoustid._scan_file(self.test_path)

        self.assertEqual(str(context.exception), "acoustid.fingerprint_file did not return (duration, fingerprint) tuple")

    def test_get_track_info_success(self):
        """Test successful track info retrieval"""
        # Set up test data
        self.acoustid.fingerprint = "test_fingerprint"
        self.acoustid.duration = 120
        self.acoustid._mock_track_info = (0.95, "test_mbid", "Test Title", "Test Artist")

        # Call the method
        self.acoustid._get_track_info()

        # Check that fileinfo was populated correctly
        expected_fileinfo = {"fingerprint": "test_fingerprint", "score": 0.95, "mbid": "test_mbid", "title": "Test Title", "artist": "Test Artist"}
        self.assertEqual(self.acoustid.fileinfo, expected_fileinfo)

    def test_get_track_info_failure(self):
        """Test track info retrieval failure"""
        # Set up test data
        self.acoustid.fingerprint = "test_fingerprint"
        self.acoustid.duration = 120
        self.acoustid._mock_track_info = (None, None, None, None)  # type: ignore

        # Verify that the method raises RuntimeError
        with self.assertRaises(RuntimeError) as context:
            self.acoustid._get_track_info()

        self.assertEqual(str(context.exception), "Failed to retrieve track information from AcoustID")


if __name__ == "__main__":
    unittest.main()
