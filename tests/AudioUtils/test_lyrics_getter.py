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

import pytest
from unittest.mock import patch, MagicMock  # noqa: F401

# Mock all required modules before importing the class under test
import sys

# Mock lyricsgenius
mock_genius = MagicMock()
sys.modules["lyricsgenius"] = mock_genius
sys.modules["lyricsgenius.genius"] = mock_genius

# Mock config and logger
mock_config = MagicMock()
mock_logger = MagicMock()
sys.modules["Singletons.config"] = mock_config
sys.modules["Singletons.logger"] = mock_logger

# Mock mutagen modules
for module_name in ["mutagen.mp4", "mutagen.apev2", "mutagen.oggvorbis", "mutagen.flac", "mutagen.mp3", "mutagen.wavpack", "mutagen.asf"]:
    sys.modules[module_name] = MagicMock()

# Now we can import the class directly
from AudioUtils.lyrics_getter import LyricsGetter  # noqa: E402


@pytest.fixture
def lyrics_getter_fixture():
    """Set up test fixtures"""
    # Reset mocks for each test
    mock_genius.reset_mock()

    # Create a mock Song object that will be returned by Genius.search_song
    mock_song = MagicMock()
    mock_song.lyrics = "Test lyrics for the song"

    # Create a mock Genius instance
    mock_genius_instance = MagicMock()
    mock_genius_instance.search_song.return_value = mock_song

    # Set up the mock Genius class to return our mock instance
    mock_genius.Genius.return_value = mock_genius_instance

    # Create an instance of LyricsGetter for each test
    lyrics_getter = LyricsGetter()

    # Return both the lyrics_getter instance and the mock_song for tests to use
    return lyrics_getter, mock_song


def test_init(lyrics_getter_fixture):
    """Test initialization of LyricsGetter"""
    lyrics_getter, _ = lyrics_getter_fixture

    # Verify that Genius was instantiated
    mock_genius.Genius.assert_called_once()

    # Verify that remove_section_headers was set to True
    assert lyrics_getter.genius.remove_section_headers is True


def test_get_lyrics_success(lyrics_getter_fixture):
    """Test successful lyrics retrieval"""
    lyrics_getter, mock_song = lyrics_getter_fixture

    # Reset the search_song mock to clear previous calls
    lyrics_getter.genius.search_song.reset_mock()  # type: ignore

    # Set up test data
    artist = "Test Artist"
    title = "Test Song"

    # Call the method
    result = lyrics_getter.get_lyrics(artist, title)

    # Verify that search_song was called with the correct parameters
    lyrics_getter.genius.search_song.assert_called_once_with(title, artist)  # type: ignore

    # Verify that the result is the mock song object
    assert result == mock_song


def test_get_lyrics_not_found(lyrics_getter_fixture):
    """Test lyrics retrieval when song is not found"""
    lyrics_getter, _ = lyrics_getter_fixture

    # Reset the search_song mock to clear previous calls
    lyrics_getter.genius.search_song.reset_mock()  # type: ignore

    # Set up test data
    artist = "Nonexistent Artist"
    title = "Nonexistent Song"

    # Configure the mock to return None (song not found)
    lyrics_getter.genius.search_song.return_value = None  # type: ignore

    # Call the method
    result = lyrics_getter.get_lyrics(artist, title)

    # Verify that search_song was called with the correct parameters
    lyrics_getter.genius.search_song.assert_called_once_with(title, artist)  # type: ignore

    # Verify that the result is None
    assert result is None


def test_get_lyrics_exception(lyrics_getter_fixture):
    """Test lyrics retrieval when an exception occurs"""
    lyrics_getter, _ = lyrics_getter_fixture

    # Reset the search_song mock to clear previous calls
    lyrics_getter.genius.search_song.reset_mock()  # type: ignore

    # Set up test data
    artist = "Exception Artist"
    title = "Exception Song"

    # Configure the mock to raise an exception
    lyrics_getter.genius.search_song.side_effect = Exception("API Error")  # type: ignore

    # Call the method and verify it handles the exception gracefully
    # Note: The current implementation doesn't handle exceptions, so we expect it to propagate
    with pytest.raises(Exception) as excinfo:
        lyrics_getter.get_lyrics(artist, title)

    # Verify the exception message
    assert str(excinfo.value) == "API Error"

    # Verify that search_song was called with the correct parameters
    lyrics_getter.genius.search_song.assert_called_once_with(title, artist)  # type: ignore
