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

"""Configuration Management Module"""

import os
import json
import logging
from pathlib import Path
ENCODING = "utf-8"

DEFAULT_CONFIG = {
    "general": {
        "debug": True,
    },
    "musicbrainz": {
        "host": "musicbrainz.org",
        "port": 443,
        "ignore_existing_acoustid_fingerprints": False,
    },
    "logging": {
        "level": "DEBUG",
        "file": "amm.log"
    },
    "paths": {
        "base": "/alpha/music/amm/",
        "import": "import/",
        "export": "export/",
        "music": "music/",
        "art": "art/",
    },
    "features": {
        "art_getter": True,
        "lyrics_getter": True,
        "normalizer": True,
        "trimmer": True,
        "converter": True,
        "file_rename": True
    },
    "extensions": {
        "import": [".mp3", ".flac", ".ogg", ".wav", ".m4a", ".aac", ".wma", ".opus", ".mp4", "mp2"],
        "export": [".mp3", ".flac"],
    },
}

class Config:
    """Configuration Management Class"""

    def __init__(self, config_file=None):
        """
        Initializes the Config class.

        Args:
            config_file: The path to the configuration file.
        """
        self.config_file = config_file or Path(__file__).parent / "config.json"
        self.config = {}
        self.load_config()

    def get_path(self, key:str) -> str:
        """
        Gets the path for the given key.

        Args:
            key: The key of the path.

        Returns:
            The path for the given key.
        """
        return self.config["paths"]["base"] + self.config["paths"][key]

    def load_config(self):
        """Loads the configuration from the file."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding=ENCODING) as f:
                self.config = json.load(f)
        else:
            logging.warning(f"Configuration file {self.config_file} not found. Using default settings.")
            self.config = DEFAULT_CONFIG
            self.save_config()

    def save_config(self):
        """Saves the configuration to the file."""
        with open(self.config_file, 'w', encoding=ENCODING) as f:
            json.dump(self.config, f, indent=4)
            logging.info(f"Configuration saved to {self.config_file}")
        self.load_config()

    def get(self, section: str, key: str, default=None) -> str | int | bool | list[str] | None:
        """
        Gets a configuration value.

        Args:
            key: The key of the configuration value.
            default: The default value to return if the key is not found.

        Returns:
            The configuration value.
        """
        return self.config[section].get(key, default)

    def set(self, section:str, key:str, value):
        """
        Sets a configuration value.
        Args:
            key: The key of the configuration value.
            value: The value to set.
        """
        self.config[section][key] = value
        self.save_config()
        logging.info(f"Configuration value {section}[{key}] set to {value}")
        self.load_config()
