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

"""This module contains the AcoustID HTTP client."""

import subprocess
import json
import aiohttp
from pathlib import Path


class AcoustIDHttpClient:
    """A class to interact with the AcoustID API."""

    async def fingerprint_file(self, path: Path) -> tuple[int, str]:
        """Generates a fingerprint for given file path.

        Args:
            path (Path): file to be fingerprinted

        Returns:
            tuple[int, str]: duration in seconds and fingerprint
        """
        result = subprocess.run(
            ["fpcalc", "-json", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return data["duration"] or 0, data["fingerprint"] or ""

    async def lookup(self, api_key: str, fingerprint: str, duration: int) -> dict:
        """Look up the information associated with the fingerprint
        in conjunction with the duration of the song.

        Args:
            api_key (str): API key for AcoustID Service
            fingerprint (str): The fingerprint of the file
            duration (int): the duration of the file in seconds

        Returns:
            dict: the results dictionairy, to be unpacked by self.parse_lookup()
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.acoustid.org/v2/lookup",
                params={
                    "client": api_key,
                    "fingerprint": fingerprint,
                    "duration": duration,
                    "meta": "recordings",
                },
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

    def parse_lookup_result(self, response: dict) -> tuple[str, str, str, dict] | None:
        """Parses the lookup result into a tuple containing the following values:
        accuracy score, MusicBrainz ID, title and artists.

        Args:
            response (dict): response given by self.lookup()

        Returns:
            tuple[str, str, str, dict]: score, mbid, title, artists
        """
        try:
            result = response["results"][
                0
            ]  # TODO: handle multiple results, keep the first for now...
            score = str(result["score"])
            recording = result["recordings"][
                0
            ]  # TODO: handle multiple results, keep the first for now...
            mbid = recording["id"]
            title = recording["title"]
            artists = recording["artists"]
            return score, mbid, title, artists
        except (KeyError, IndexError):
            return None
