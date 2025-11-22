# models.py

from pydantic import BaseModel, Field
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


class AppConfig(BaseModel):
    version: str
    general: GeneralConfig
    musicbrainz: MusicBrainzConfig
    logging: LoggingConfig
    paths: PathsConfig
    extensions: ExtensionsConfig
