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
from unittest.mock import AsyncMock
import pytest

pytest.importorskip("aiohttp")

from plugins.audio_utils.mb_client import MusicBrainzClient


def test_get_by_id_delegates_to_request():
    client = MusicBrainzClient()
    client._request = AsyncMock(return_value={"ok": True})

    result = asyncio.run(client.get_artist_by_id("abc"))

    assert result == {"ok": True}
    client._request.assert_awaited_once_with("artist/abc", {"fmt": "json"})


def test_get_art_delegates_to_cover_request():
    client = MusicBrainzClient()
    client._request_cover = AsyncMock(return_value="http://image")

    result = asyncio.run(client.get_art("mbid123"))

    assert result == "http://image"
    client._request_cover.assert_awaited_once_with("mbid123")
