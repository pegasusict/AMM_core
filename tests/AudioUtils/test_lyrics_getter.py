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
from types import SimpleNamespace
from unittest.mock import patch

from plugins.audio_utils.lyrics_getter_util import LyricsGetter


class _FakeConfig:
    def __init__(self, token: str | None) -> None:
        self._token = token

    def get(
        self,
        section: str,
        key: str | None = None,
        default: object = None,
    ) -> object:
        if section in {"genius_api_token", "genius_access_token"} and key is None:
            return self._token
        return default


class _FakeSong:
    def __init__(self, lyrics: str) -> None:
        self.lyrics = lyrics


class _FakeGeniusClient:
    def __init__(self, song: _FakeSong | None) -> None:
        self.song = song
        self.calls: list[tuple[str, str | None]] = []

    def search_song(self, title: str, artist: str | None = None) -> _FakeSong | None:
        self.calls.append((title, artist))
        return self.song


def _build_lyrics_getter(
    song: _FakeSong | None = None,
    token: str | None = "token",
) -> tuple[LyricsGetter, _FakeGeniusClient]:
    fake_client = _FakeGeniusClient(song=song)
    fake_module = SimpleNamespace(Genius=lambda *args, **kwargs: fake_client)
    with (
        patch(
            "plugins.audio_utils.lyrics_getter_util.Config.get_sync",
            return_value=_FakeConfig(token),
        ),
        patch("plugins.audio_utils.lyrics_getter_util.lyricsgenius", fake_module),
    ):
        lg = LyricsGetter()
    return lg, fake_client


def test_get_lyrics_success() -> None:
    lg, fake_client = _build_lyrics_getter(_FakeSong("Line 1\nLine 2\n123Embed"))
    result = asyncio.run(lg.get_lyrics("Artist - Title"))
    assert result == "Line 1\nLine 2"
    assert fake_client.calls[0] == ("Title", "Artist")


def test_get_lyrics_not_found() -> None:
    lg, _ = _build_lyrics_getter(song=None)
    result = asyncio.run(lg.get_lyrics("Artist - Missing"))
    assert result is None


def test_get_lyrics_without_token() -> None:
    lg, _ = _build_lyrics_getter(_FakeSong("lyrics"), token=None)
    result = asyncio.run(lg.get_lyrics("Artist - Title"))
    assert result is None
