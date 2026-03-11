import asyncio
import json
import subprocess
import aiohttp
from pathlib import Path

from Singletons import Logger


logger = Logger()


class AcoustIDHttpClient:
    async def fingerprint_file(self, path: Path) -> tuple[int, str]:
        result = subprocess.run(
            ["fpcalc", "-json", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            logger.warning(
                f"fpcalc returned non-zero exit code {result.returncode} for {path}: {stderr}"
            )
        if not result.stdout:
            raise RuntimeError("fpcalc produced no output")
        data = json.loads(result.stdout)
        return data["duration"], data["fingerprint"]

    async def lookup(self, api_key: str, fingerprint: str, duration: int) -> dict:
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                payload = {
                    "client": api_key,
                    "fingerprint": fingerprint,
                    "duration": int(duration),
                    "meta": "recordings",
                }
                async with session.post(
                    "https://api.acoustid.org/v2/lookup",
                    data=payload,
                ) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except asyncio.TimeoutError as exc:
            logger.error("AcoustID lookup timed out.")
            raise exc
        except aiohttp.ClientError as exc:
            logger.error(f"AcoustID lookup failed: {exc}")
            raise

    def parse_lookup_result(
        self, response: dict
    ) -> tuple[float, str, str, list[dict[str, str]]] | None:
        try:
            results = response.get("results") or []
            if not results:
                return None

            result = results[0]
            score = float(result.get("score") or 0)

            recordings = result.get("recordings") or []
            if not recordings:
                return None

            recording = recordings[0]
            mbid = str(recording.get("id") or "")
            title = str(recording.get("title") or "")

            artists: list[dict[str, str]] = []
            for artist in recording.get("artists") or []:
                name = artist.get("name")
                if not name:
                    continue
                artists.append(
                    {"name": str(name), "mbid": str(artist.get("id") or "")}
                )

            return score, mbid, title, artists
        except Exception:
            return None
