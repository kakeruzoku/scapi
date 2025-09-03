from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Final

from scapi.sites.session import Session
from scapi.utils.client import HTTPClient
from .base import _BaseSiteAPI
from ..utils.types import (
    ScratchNewsPayload
)
from ..utils.common import (
    UNKNOWN,
    UNKNOWN_TYPE,
    MAYBE_UNKNOWN,
    dt_from_isoformat,
    api_iterative,
    split
)
if TYPE_CHECKING:
    from .session import Session
    from ..utils.client import HTTPClient

class News(_BaseSiteAPI):
    """
    Scratchのニュース欄

    Attributes:
        id (int):
        headline (str): ニュースのタイトル
        url (str): 詳細へのリンク
        image (str): アイコンの画像のurl
        copy (str): 説明文
    """
    def __init__(self, id:int, client_or_session:"HTTPClient|Session|None") -> None:
        super().__init__(client_or_session)

        self.id:Final[int] = id
        self._created_at:MAYBE_UNKNOWN[str] = UNKNOWN
        self.headline:MAYBE_UNKNOWN[str] = UNKNOWN
        self.url:MAYBE_UNKNOWN[str] = UNKNOWN
        self.image:MAYBE_UNKNOWN[str] = UNKNOWN
        self.copy:MAYBE_UNKNOWN[str] = UNKNOWN

    def __str__(self) -> str:
        return f"<News id:{self.id} headline:{self.headline}>"

    def _update_from_data(self, data:ScratchNewsPayload):
        self._created_at = data.get("stamp")
        self.headline = data.get("headline")
        self.url = data.get("url")
        self.image = data.get("image")
        self.copy = data.get("copy")

    @property
    def created_at(self) -> datetime.datetime|UNKNOWN_TYPE:
        """
        ニュースが投稿された時間を返す

        .. warning::
            APIの情報が不正確だと考えられます。データの利用時には注意してください。

        Returns:
            datetime.datetime|UNKNOWN_TYPE:
        """
        return dt_from_isoformat(self._created_at)
    
async def get_news(
        client:"HTTPClient",
        limit:int|None=None,offset:int|None=None
        
    ) -> AsyncGenerator[News]:
    """
    ニュースを取得する。

    Args:
        client (HTTPClient): 使用するHTTPクライアント
        limit (int|None, optional): 取得するニュースの数。初期値は40です。
        offset (int|None, optional): 取得するニュースの開始位置。初期値は0です。

    Yields:
        News:
    """
    async for _p in api_iterative(
        client,f"https://api.scratch.mit.edu/news",
        limit=limit,offset=offset
    ):
        yield News._create_from_data(_p["id"],_p,client)