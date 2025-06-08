from pathlib import Path
from typing import Optional
from mutagen import File


class SimpleTagger:
    def __init__(self, path: Path) -> None:
        """Initializes the SimpleTagger with a file path."""
        self.audio = File(path)

    def get_mbid(self) -> Optional[str]:
        """Retrieves the MusicBrainz ID (MBID) from the audio file tags."""
        # Fallback to 'mbid' if 'musicbrainz_trackid' is not present
        return self.audio.tags.get("musicbrainz_trackid", [None])[0] or self.audio.tags.get("mbid", [None])[0]  # type: ignore

    def get_acoustid(self) -> Optional[str]:
        """Retrieves the AcoustID from the audio file tags."""
        # Fallback to 'acoustid' if 'acoustid_id' is not present
        return self.audio.tags.get("acoustid_id", [None])[0] or self.audio.tags.get("acoustid", [None])[0]  # type: ignore
