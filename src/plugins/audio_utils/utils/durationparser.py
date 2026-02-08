from mutagen import File
from pathlib import Path


class DurationParser:
    """A class to parse the duration of audio files using Mutagen."""

    def get_duration(self, path: Path) -> int:
        """Returns the duration of the audio file in seconds."""
        audio = File(path)
        return int(audio.info.length)  # type: ignore
