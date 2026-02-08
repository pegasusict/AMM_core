import subprocess
import json
import aiohttp
from pathlib import Path


class AcoustIDHttpClient:
    async def fingerprint_file(self, path: Path) -> tuple[int, str]:
        result = subprocess.run(
            ["fpcalc", "-json", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return data["duration"], data["fingerprint"]

    async def lookup(self, api_key: str, fingerprint: str, duration: int) -> dict:
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

    def parse_lookup_result(self, response: dict) -> tuple[str, str, str, str]:
        try:
            result = response["results"][0]
            score = str(result["score"])
            recording = result["recordings"][0]
            mbid = recording["id"]
            title = recording["title"]
            artist = recording["artists"][0]["name"]
            return score, mbid, title, artist
        except (KeyError, IndexError):
            return "", "", "", ""
