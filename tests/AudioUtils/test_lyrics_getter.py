# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
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

import asyncio
import pytest
from unittest.mock import patch

pytest.importorskip("aiohttp")

from plugins.audio_utils.lyrics_getter_util import LyricsGetter


class _MockResponse:
    def __init__(self, status: int, payload: dict):
        self.status = status
        self._payload = payload

    async def json(self):
        return self._payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _MockSession:
    def __init__(self, response: _MockResponse):
        self._response = response

    def get(self, *args, **kwargs):
        return self._response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_get_lyrics_success():
    lg = LyricsGetter()
    lg.provider_url = "http://example.com"

    response = _MockResponse(200, {"lyrics": "Test lyrics"})
    session = _MockSession(response)

    with patch("aiohttp.ClientSession", return_value=session):
        result = asyncio.run(lg.get_lyrics("Artist - Title"))

    assert result == "Test lyrics"


def test_get_lyrics_not_found():
    lg = LyricsGetter()
    lg.provider_url = "http://example.com"

    response = _MockResponse(200, {"lyrics": None})
    session = _MockSession(response)

    with patch("aiohttp.ClientSession", return_value=session):
        result = asyncio.run(lg.get_lyrics("Artist - Missing"))

    assert result is None


def test_get_lyrics_http_error():
    lg = LyricsGetter()
    lg.provider_url = "http://example.com"

    response = _MockResponse(500, {})
    session = _MockSession(response)

    with patch("aiohttp.ClientSession", return_value=session):
        result = asyncio.run(lg.get_lyrics("Artist - Error"))

    assert result is None
