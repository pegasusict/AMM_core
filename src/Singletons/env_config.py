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

"""Environment config file reader"""

from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class EnvConfig(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+asyncmy://user:password@localhost:3306/musicdb"

    # Google OAuth2
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # Admin password fallback
    ADMIN_EMAILS: List[str] = []
    ADMIN_PASSWORD_HASH: str = ""  # e.g., bcrypt hashed

    # Icecast per-user stream base URL
    ICECAST_HOST: str = "localhost"
    ICECAST_PORT: int = 8000
    ICECAST_MOUNT_TEMPLATE: str = "/stream/{username}.ogg"  # auto-resolved per user

    # General
    DEBUG: bool = False
    SECRET_KEY: str = "supersecretkey"  # FastAPI session/cookie signing

    class Config:
        env_file = Path(__file__).parent / ".env"  # or wherever you want


env_config = EnvConfig()
