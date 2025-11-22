# defaults.py

CONFIG_VERSION = "1.0"

DEFAULT_CONFIG = {
    "version": "1.0",
    "general": {"clean": True},
    "musicbrainz": {
        "host": "musicbrainz.org",
        "port": 443,
        "ignore_existing_acoustid_fingerprints": False,
    },
    "logging": {"level": "DEBUG", "file": "amm.log"},
    "paths": {
        "base": "/alpha/music/amm/",
        "import": "import/",
        "process": "process/",
        "export": "export/",
        "music": "music/",
        "art": "art/",
    },
    "extensions": {
        "import": [
            "mp3","flac","ogg","wav","m4a","aac",
            "wma","opus","mp4","mp2",
        ],
        "export": ["mp3", "flac"],
    },
}
