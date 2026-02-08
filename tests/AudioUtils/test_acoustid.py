import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock

pytest.importorskip("pydantic")

from plugins.audio_utils.acoustid import AcoustID
from core.exceptions import FileError, OperationFailedError


@pytest.fixture
def path():
    return Path("/music/test_song.flac")


@pytest.fixture
def acoustid_client():
    client = Mock()
    client.fingerprint_file = AsyncMock(return_value=(240, "abc123fingerprint"))
    client.lookup = AsyncMock(return_value="dummy_response")
    client.parse_lookup_result = Mock(
        return_value=(0.99, "mbid123", "Song Title", {"artists": ["Artist Name"]})
    )
    return client


@pytest.fixture
def parser():
    parser = Mock()
    parser.get_duration = AsyncMock(return_value=240)
    return parser


@pytest.fixture
def tagger_with_mbid():
    tagger = Mock()
    tagger.get_mbid = AsyncMock(return_value="mbid-from-tags")
    return tagger


@pytest.fixture
def tagger_without_mbid():
    tagger = Mock()
    tagger.get_mbid = AsyncMock(return_value=None)
    return tagger


def test_process_with_mbid_from_tags(path, acoustid_client, tagger_with_mbid, parser):
    handler = AcoustID(
        tagger=tagger_with_mbid,
        media_parser=parser,
        acoustid_client=acoustid_client,
    )
    result = asyncio.run(handler.process(path, api_key="fake_key"))

    assert result["mbid"] == "mbid-from-tags"
    acoustid_client.fingerprint_file.assert_not_called()
    acoustid_client.lookup.assert_not_called()


def test_process_with_fingerprint_fallback(path, acoustid_client, tagger_without_mbid, parser):
    handler = AcoustID(
        tagger=tagger_without_mbid,
        media_parser=parser,
        acoustid_client=acoustid_client,
    )
    result = asyncio.run(handler.process(path, api_key="fake_key"))

    assert result["mbid"] == "mbid123"
    assert result["title"] == "Song Title"
    assert result["mbid"] == "mbid123"
    acoustid_client.lookup.assert_awaited_once()
    acoustid_client.fingerprint_file.assert_awaited_once()


def test_process_missing_extension_raises(path, acoustid_client, tagger_with_mbid, parser):
    bad_path = Path("/music/no_extension")
    handler = AcoustID(
        tagger=tagger_with_mbid,
        media_parser=parser,
        acoustid_client=acoustid_client,
    )
    with pytest.raises(FileError):
        asyncio.run(handler.process(bad_path, api_key="fake_key"))


def test_fingerprint_failure_raises(path, acoustid_client, tagger_without_mbid, parser):
    acoustid_client.fingerprint_file.side_effect = Exception("fingerprint error")

    handler = AcoustID(
        tagger=tagger_without_mbid,
        media_parser=parser,
        acoustid_client=acoustid_client,
    )
    with pytest.raises(OperationFailedError, match="Could not generate fingerprint"):
        asyncio.run(handler.process(path, api_key="fake_key"))


def test_lookup_failure_raises(path, acoustid_client, tagger_without_mbid, parser):
    acoustid_client.lookup.side_effect = Exception("lookup failure")

    handler = AcoustID(
        tagger=tagger_without_mbid,
        media_parser=parser,
        acoustid_client=acoustid_client,
    )

    with pytest.raises(OperationFailedError, match="Lookup failed"):
        asyncio.run(handler.process(path, api_key="fake_key"))
