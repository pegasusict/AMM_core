import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from AudioUtils.acoustid import AcoustID
from Exceptions import FileError, OperationFailedError


@pytest.fixture
def path():
    return Path("/music/test_song.flac")


@pytest.fixture
def logger():
    return Mock()


@pytest.fixture
def acoustid_client():
    client = Mock()
    client.fingerprint_file = AsyncMock(return_value=(240, "abc123fingerprint"))
    client.lookup = AsyncMock(return_value="dummy_response")
    client.parse_lookup_result = Mock(return_value=("0.99", "mbid123", "Song Title", "Artist Name"))
    return client


@pytest.fixture
def parser():
    parser = Mock()
    parser.get_duration.return_value = 240
    return parser


@pytest.fixture
def tagger_with_mbid():
    tagger = Mock()
    tagger.get_mbid.return_value = "mbid-from-tags"
    tagger.get_acoustid.return_value = None
    return tagger


@pytest.fixture
def tagger_without_mbid():
    tagger = Mock()
    tagger.get_mbid.return_value = None
    tagger.get_acoustid.return_value = None
    return tagger


@pytest.mark.asyncio
async def test_process_with_mbid_from_tags(path, acoustid_client, tagger_with_mbid, parser, logger):
    handler = AcoustID(path=path, acoustid_client=acoustid_client, tagger=tagger_with_mbid, parser=parser, logger=logger, api_key="fake_key")
    result = await handler.process()

    assert result["mbid"] == "mbid-from-tags"
    acoustid_client.fingerprint_file.assert_not_called()
    acoustid_client.lookup.assert_not_called()


@pytest.mark.asyncio
async def test_process_with_fingerprint_fallback(path, acoustid_client, tagger_without_mbid, parser, logger):
    handler = AcoustID(path=path, acoustid_client=acoustid_client, tagger=tagger_without_mbid, parser=parser, logger=logger, api_key="fake_key")
    result = await handler.process()

    assert result["mbid"] == "mbid123"
    assert result["title"] == "Song Title"
    assert result["fingerprint"] == "abc123fingerprint"
    acoustid_client.lookup.assert_awaited_once()
    acoustid_client.fingerprint_file.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_missing_extension_raises(path, acoustid_client, tagger_with_mbid, parser, logger):
    bad_path = Path("/music/no_extension")
    handler = AcoustID(path=bad_path, acoustid_client=acoustid_client, tagger=tagger_with_mbid, parser=parser, logger=logger, api_key="fake_key")
    with pytest.raises(FileError):
        await handler.process()


@pytest.mark.asyncio
async def test_fingerprint_failure_raises(path, acoustid_client, tagger_without_mbid, parser, logger):
    acoustid_client.fingerprint_file.side_effect = Exception("fingerprint error")

    handler = AcoustID(path=path, acoustid_client=acoustid_client, tagger=tagger_without_mbid, parser=parser, logger=logger, api_key="fake_key")
    with pytest.raises(OperationFailedError, match="Could not generate fingerprint"):
        await handler.process()


@pytest.mark.asyncio
async def test_lookup_failure_raises(path, acoustid_client, tagger_without_mbid, parser, logger):
    acoustid_client.lookup.side_effect = Exception("lookup failure")

    handler = AcoustID(path=path, acoustid_client=acoustid_client, tagger=tagger_without_mbid, parser=parser, logger=logger, api_key="fake_key")

    # Pre-load fingerprint to skip _scan_file
    handler.fingerprint = "preset"
    handler.duration = 240

    with pytest.raises(OperationFailedError, match="Lookup failed"):
        await handler.process()
