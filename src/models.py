from pydantic import BaseModel, validator
from typing import List, Optional


class ArtistModel(BaseModel):
    name: str
    mbid: Optional[str] = None


class MetadataModel(BaseModel):
    artists: List[ArtistModel] = []
    title: Optional[str] = None
    mbid: Optional[str] = None
