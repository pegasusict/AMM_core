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
from unittest.mock import MagicMock

# Mock all required modules before importing the class under test
import sys
from enum import StrEnum, auto


# Create real exception classes for musicbrainzngs
class NetworkError(Exception):
    pass


class WebServiceError(Exception):
    pass


class ResponseError(Exception):
    pass


# Create a real MBQueryType enum
class MBQueryType(StrEnum):
    ARTIST = auto()
    ALBUM = auto()
    RELEASE = auto()
    TRACK = auto()
    RECORDING = auto()
    RELEASE_GROUP = auto()


# Create a real InvalidValueError
class InvalidValueError(Exception):
    pass


# Mock musicbrainzngs
mock_musicbrainzngs = MagicMock()
mock_musicbrainzngs.NetworkError = NetworkError
mock_musicbrainzngs.WebServiceError = WebServiceError
mock_musicbrainzngs.ResponseError = ResponseError
sys.modules["musicbrainzngs"] = mock_musicbrainzngs

# Mock config and logger
mock_config = MagicMock()
mock_logger = MagicMock()
logger_instance = MagicMock()
mock_logger.Logger.return_value = logger_instance
sys.modules["Singletons.config"] = mock_config
sys.modules["Singletons.logger"] = mock_logger

# Mock Enums and Exceptions
mock_enums = MagicMock()
mock_enums.MBQueryType = MBQueryType
mock_exceptions = MagicMock()
mock_exceptions.InvalidValueError = InvalidValueError
sys.modules["Enums"] = mock_enums
sys.modules["Exceptions"] = mock_exceptions

# Now we can import the class directly
from AudioUtils.mb_client import MusicBrainzClient  # noqa: E402


@pytest.fixture
def mb_client_fixture():
    """Fixture to set up MusicBrainzClient for tests"""
    # Reset mocks for each test
    mock_musicbrainzngs.reset_mock()
    mock_config.reset_mock()
    mock_logger.reset_mock()
    logger_instance.reset_mock()

    # Create a mock Config instance
    mock_config_instance = MagicMock()

    # Create an instance of MusicBrainzClient
    mb_client = MusicBrainzClient(mock_config_instance)

    # Set the logger instance
    mb_client.logger = logger_instance

    # Set up common test data
    test_data = {
        "mbid": "12345678-1234-1234-1234-123456789012",
        "name": "Test Name",
        "fingerprint": "test_fingerprint_data",
        "config_instance": mock_config_instance,
    }

    return mb_client, test_data


def test_init(mb_client_fixture):
    """Test initialization of MusicBrainzClient"""
    mb_client, test_data = mb_client_fixture
    mock_config_instance = test_data["config_instance"]

    # Verify that the logger was initialized with the config
    mock_logger.Logger.assert_called_once_with(mock_config_instance)

    # Verify that the config was stored
    assert mb_client.config == mock_config_instance

    # Verify that musicbrainzngs was stored
    assert mb_client.musicbrainz == mock_musicbrainzngs

    # Verify that useragent was set
    mock_musicbrainzngs.set_useragent.assert_called_once_with("Audiophiles' Music Manager", "0.1", "pegasus.ict@gmail.com")

    # Verify that rate limit was set
    mock_musicbrainzngs.set_rate_limit.assert_called_once_with(True)


def test_get_art_success(mb_client_fixture):
    """Test successful art retrieval"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock response
    mock_response = {"images": [{"thumbnails": {"large": "http://example.com/image.jpg"}}]}
    mock_musicbrainzngs.get_image_list.return_value = mock_response

    # Make sure the mock response is properly structured
    # This is needed because MagicMock doesn't automatically create the expected structure
    def get_image_list_side_effect(mbid):
        return mock_response

    mock_musicbrainzngs.get_image_list.side_effect = get_image_list_side_effect

    # Call the method
    result = mb_client.get_art(test_mbid)

    # Verify that get_image_list was called with the correct parameters
    mock_musicbrainzngs.get_image_list.assert_called_once_with(test_mbid)

    # Verify that the result is the expected URL
    assert result == "http://example.com/image.jpg"


def test_get_art_no_images(mb_client_fixture):
    """Test art retrieval when no images are found"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock response with no images
    mock_response = {"images": []}

    # Make sure the mock response is properly structured
    def get_image_list_side_effect(mbid):
        return mock_response

    mock_musicbrainzngs.get_image_list.side_effect = get_image_list_side_effect

    # Call the method
    result = mb_client.get_art(test_mbid)

    # Verify that get_image_list was called with the correct parameters
    mock_musicbrainzngs.get_image_list.assert_called_once_with(test_mbid)

    # Verify that the result is None
    assert result is None


def test_get_art_network_error(mb_client_fixture):
    """Test art retrieval when a network error occurs"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock to raise an exception
    mock_musicbrainzngs.get_image_list.side_effect = NetworkError("Network error")

    # Call the method
    result = mb_client.get_art(test_mbid)

    # Verify that get_image_list was called with the correct parameters
    mock_musicbrainzngs.get_image_list.assert_called_once_with(test_mbid)

    # Verify that the error was logged
    logger_instance.error.assert_called_once()

    # Verify that the result is None
    assert result is None


def test_get_by_id_artist(mb_client_fixture):
    """Test getting artist by ID"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock response
    mock_response = {"artist": {"name": "Test Artist"}}
    mock_musicbrainzngs.get_artist_by_id.return_value = mock_response

    # Call the method
    result = mb_client._get_by_id(MBQueryType.ARTIST, test_mbid)

    # Verify that get_artist_by_id was called with the correct parameters
    mock_musicbrainzngs.get_artist_by_id.assert_called_once_with(test_mbid)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_by_id_recording(mb_client_fixture):
    """Test getting recording by ID"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock response
    mock_response = {"recording": {"title": "Test Recording"}}
    mock_musicbrainzngs.get_recording_by_id.return_value = mock_response

    # Call the method
    result = mb_client._get_by_id(MBQueryType.RECORDING, test_mbid)

    # Verify that get_recording_by_id was called with the correct parameters
    mock_musicbrainzngs.get_recording_by_id.assert_called_once_with(test_mbid)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_by_id_track(mb_client_fixture):
    """Test getting track by ID"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock response
    mock_response = {"recording": {"title": "Test Track"}}
    mock_musicbrainzngs.get_recording_by_id.return_value = mock_response

    # Call the method
    result = mb_client._get_by_id(MBQueryType.TRACK, test_mbid)

    # Verify that get_recording_by_id was called with the correct parameters
    mock_musicbrainzngs.get_recording_by_id.assert_called_once_with(test_mbid)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_by_id_release(mb_client_fixture):
    """Test getting release by ID"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock response
    mock_response = {"release": {"title": "Test Release"}}
    mock_musicbrainzngs.get_release_by_id.return_value = mock_response

    # Call the method
    result = mb_client._get_by_id(MBQueryType.RELEASE, test_mbid)

    # Verify that get_release_by_id was called with the correct parameters
    mock_musicbrainzngs.get_release_by_id.assert_called_once_with(test_mbid)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_by_id_album(mb_client_fixture):
    """Test getting album by ID"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock response
    mock_response = {"release": {"title": "Test Album"}}
    mock_musicbrainzngs.get_release_by_id.return_value = mock_response

    # Call the method
    result = mb_client._get_by_id(MBQueryType.ALBUM, test_mbid)

    # Verify that get_release_by_id was called with the correct parameters
    mock_musicbrainzngs.get_release_by_id.assert_called_once_with(test_mbid)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_by_id_release_group(mb_client_fixture):
    """Test getting release group by ID"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock response
    mock_response = {"release-group": {"title": "Test Release Group"}}
    mock_musicbrainzngs.get_release_group_by_id.return_value = mock_response

    # Call the method
    result = mb_client._get_by_id(MBQueryType.RELEASE_GROUP, test_mbid)

    # Verify that get_release_group_by_id was called with the correct parameters
    mock_musicbrainzngs.get_release_group_by_id.assert_called_once_with(test_mbid)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_by_id_invalid_type(mb_client_fixture):
    """Test getting by ID with an invalid query type"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock for InvalidValueError
    mock_exceptions.InvalidValueError = Exception

    # Call the method with an invalid query type and verify it raises an exception
    with pytest.raises(Exception):
        mb_client._get_by_id("INVALID_TYPE", test_mbid)


def test_get_by_id_response_error(mb_client_fixture):
    """Test getting by ID when a response error occurs"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Set up mock to raise an exception
    mock_musicbrainzngs.get_artist_by_id.side_effect = ResponseError("Response error")

    # Call the method
    result = mb_client._get_by_id(MBQueryType.ARTIST, test_mbid)

    # Verify that get_artist_by_id was called with the correct parameters
    mock_musicbrainzngs.get_artist_by_id.assert_called_once_with(test_mbid)

    # Verify that the error was logged
    logger_instance.error.assert_called_once()

    # Verify that the result is None
    assert result is None


def test_get_by_name_artist(mb_client_fixture):
    """Test getting artist by name"""
    mb_client, test_data = mb_client_fixture
    test_name = test_data["name"]

    # Set up mock response
    mock_response = {"artist-list": [{"name": "Test Artist"}]}
    mock_musicbrainzngs.search_artists.return_value = mock_response

    # Call the method
    result = mb_client._get_by_name(MBQueryType.ARTIST, test_name)

    # Verify that search_artists was called with the correct parameters
    mock_musicbrainzngs.search_artists.assert_called_once_with(name=test_name)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_by_name_album(mb_client_fixture):
    """Test getting album by name"""
    mb_client, test_data = mb_client_fixture
    test_name = test_data["name"]

    # Set up mock response
    mock_response = {"release-list": [{"title": "Test Album"}]}
    mock_musicbrainzngs.search_releases.return_value = mock_response

    # Call the method
    result = mb_client._get_by_name(MBQueryType.ALBUM, test_name)

    # Verify that search_releases was called with the correct parameters
    mock_musicbrainzngs.search_releases.assert_called_once_with(name=test_name)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_by_name_track(mb_client_fixture):
    """Test getting track by name"""
    mb_client, test_data = mb_client_fixture
    test_name = test_data["name"]

    # Set up mock response
    mock_response = {"recording-list": [{"title": "Test Track"}]}
    mock_musicbrainzngs.search_recordings.return_value = mock_response

    # Call the method
    result = mb_client._get_by_name(MBQueryType.TRACK, test_name)

    # Verify that search_recordings was called with the correct parameters
    mock_musicbrainzngs.search_recordings.assert_called_once_with(name=test_name)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_by_name_invalid_type(mb_client_fixture):
    """Test getting by name with an invalid query type"""
    mb_client, test_data = mb_client_fixture
    test_name = test_data["name"]

    # Set up mock for InvalidValueError
    mock_exceptions.InvalidValueError = Exception

    # Call the method with an invalid query type and verify it raises an exception
    with pytest.raises(Exception):
        mb_client._get_by_name("INVALID_TYPE", test_name)


def test_get_track_by_audio_fingerprint(mb_client_fixture):
    """Test getting track by audio fingerprint"""
    mb_client, test_data = mb_client_fixture
    test_fingerprint = test_data["fingerprint"]

    # Set up mock response
    mock_response = {"recording-list": [{"title": "Test Track"}]}
    mock_musicbrainzngs.search_recordings.return_value = mock_response

    # Call the method
    result = mb_client.get_track_by_audio_fingerprint(test_fingerprint)

    # Verify that search_recordings was called with the correct parameters
    mock_musicbrainzngs.search_recordings.assert_called_once_with(fingerprint=test_fingerprint)

    # Verify that the result is the expected response
    assert result == mock_response


def test_get_track_by_audio_fingerprint_error(mb_client_fixture):
    """Test getting track by audio fingerprint when an error occurs"""
    mb_client, test_data = mb_client_fixture
    test_fingerprint = test_data["fingerprint"]

    # Set up mock to raise an exception
    mock_musicbrainzngs.search_recordings.side_effect = NetworkError("Network error")

    # Call the method
    result = mb_client.get_track_by_audio_fingerprint(test_fingerprint)

    # Verify that search_recordings was called with the correct parameters
    mock_musicbrainzngs.search_recordings.assert_called_once_with(fingerprint=test_fingerprint)

    # Verify that the error was logged
    logger_instance.error.assert_called_once()

    # Verify that the result is None
    assert result is None


# Test the public wrapper methods
def test_get_artist_by_id(mb_client_fixture):
    """Test get_artist_by_id wrapper method"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Mock the _get_by_id method
    mb_client._get_by_id = MagicMock(return_value={"artist": {"name": "Test Artist"}})

    # Call the method
    result = mb_client.get_artist_by_id(test_mbid)

    # Verify that _get_by_id was called with the correct parameters
    mb_client._get_by_id.assert_called_once_with(MBQueryType.ARTIST, test_mbid)

    # Verify that the result is the expected response
    assert result == {"artist": {"name": "Test Artist"}}


def test_get_release_by_id(mb_client_fixture):
    """Test get_release_by_id wrapper method"""
    mb_client, test_data = mb_client_fixture
    test_mbid = test_data["mbid"]

    # Mock the _get_by_id method
    mb_client._get_by_id = MagicMock(return_value={"release": {"title": "Test Release"}})

    # Call the method
    result = mb_client.get_release_by_id(test_mbid)

    # Verify that _get_by_id was called with the correct parameters
    mb_client._get_by_id.assert_called_once_with(MBQueryType.RELEASE, test_mbid)

    # Verify that the result is the expected response
    assert result == {"release": {"title": "Test Release"}}


def test_get_artist_by_name(mb_client_fixture):
    """Test get_artist_by_name wrapper method"""
    mb_client, test_data = mb_client_fixture
    test_name = test_data["name"]

    # Mock the _get_by_name method
    mb_client._get_by_name = MagicMock(return_value={"artist-list": [{"name": "Test Artist"}]})

    # Call the method
    result = mb_client.get_artist_by_name(test_name)

    # Verify that _get_by_name was called with the correct parameters
    mb_client._get_by_name.assert_called_once_with(MBQueryType.ARTIST, test_name)

    # Verify that the result is the expected response
    assert result == {"artist-list": [{"name": "Test Artist"}]}
