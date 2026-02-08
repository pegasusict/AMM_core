# models.py

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import List


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "amm.log"


class PathsConfig(BaseModel):
    base: str
    import_: str = Field(default="import/", alias="import")
    process: str = "process/"
    export: str = "export/"
    music: str = "music/"
    art: str = "art/"


class GeneralConfig(BaseModel):
    clean: bool = True


class MusicBrainzConfig(BaseModel):
    host: str
    port: int
    ignore_existing_acoustid_fingerprints: bool


class ExtensionsConfig(BaseModel):
    import_: List[str] = Field(alias="import")
    export: List[str]


class AuthConfig(BaseModel):
    google_client_id: str = ""
    google_client_secret: str = ""
    admin_usernames: List[str] = []
    allowed_usernames: List[str] = []
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: str
    general: GeneralConfig
    musicbrainz: MusicBrainzConfig
    logging: LoggingConfig
    paths: PathsConfig
    extensions: ExtensionsConfig
    auth: AuthConfig = AuthConfig()
