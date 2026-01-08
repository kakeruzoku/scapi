from __future__ import annotations

from enum import Enum
from typing import Final,TYPE_CHECKING

from ..utils.client import HTTPClient
from ..utils.common import (
    MAYBE_UNKNOWN,
    UNKNOWN,
)
from .base import _BaseSiteAPI
from ..utils.types import (
    BackpackPayload
)

if TYPE_CHECKING:
    from .session import Session

class BackpackType(Enum):
    Unknown=0
    Sprite=1
    Script=2
    BitmapCostume=3
    VectorCostume=4
    Sound=5

type_to_mime = {
    BackpackType.Sprite:("sprite","application/zip"),
    BackpackType.Script:("script","application/json"),
    BackpackType.BitmapCostume:("costume","image/png"),
    BackpackType.VectorCostume:("costume","image/svg+xml"),
    BackpackType.Sound:("sound","audio/x-wav"),
}

mime_to_type = {v:k for k,v in type_to_mime.items()}

class Backpack(_BaseSiteAPI[str]):
    def __init__(self,id:str,client_or_session: HTTPClient | Session | None) -> None:
        super().__init__(client_or_session)

        self.id:Final[str] = id
        self.type:MAYBE_UNKNOWN[BackpackType] = UNKNOWN
        self.name:MAYBE_UNKNOWN[str] = UNKNOWN
        self.body:MAYBE_UNKNOWN[str] = UNKNOWN
        self.thumbnail:MAYBE_UNKNOWN[str] = UNKNOWN

    def __eq__(self, value:object) -> bool:
        return isinstance(value,Backpack) and self.id == value.id

    def _update_from_data(self, data:BackpackPayload):
        self.type = mime_to_type.get((data.get("type"),data.get("mime")),BackpackType.Unknown)
        self._update_to_attributes(
            name=data.get("name"),
            body=data.get("body"),
            thumbnail=data.get("thumbnail")
        )

    @property
    def body_url(self) -> str:
        assert self.body is not UNKNOWN
        return f"https://backpack.scratch.mit.edu/{self.body}"
    
    @property
    def thumbnail_url(self):
        assert self.thumbnail is not UNKNOWN
        return f"https://backpack.scratch.mit.edu/{self.thumbnail}"

    async def delete(self):
        await self.client.delete(f"https://backpack.scratch.mit.edu/{self._session.username}/{self.id}")