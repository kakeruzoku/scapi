from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final

import aiohttp
import bs4
from ..utils.client import HTTPClient
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    _AwaitableContextManager,
    temporary_httpclient,
    split
)

from .base import _BaseSiteAPI

if TYPE_CHECKING:
    from .session import Session

class ForumCategory(_BaseSiteAPI[int]):
    def __init__(self,id:int,client_or_session:"HTTPClient|Session|None"=None):
        super().__init__(client_or_session)
        self.id:Final[int] = id

        self.name:MAYBE_UNKNOWN[str] = UNKNOWN

        self.box_name:MAYBE_UNKNOWN[str] = UNKNOWN
        self.description:MAYBE_UNKNOWN[str] = UNKNOWN
        self.topic_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.post_count:MAYBE_UNKNOWN[int] = UNKNOWN
        #self.last_post

    def __repr__(self) -> str:
        return f"<ForumCategory id:{self.id} name:{self.name}>"

    @classmethod
    def _create_from_home(
        cls,
        box_name:str,
        data:bs4.Tag,
        client_or_session:"HTTPClient|Session|None"=None
    ):
        _title:bs4.Tag|Any = data.find("div",{"class":"tclcon"})
        _name:bs4.Tag|Any = _title.find("a")
        _url:str|Any = _name["href"]

        category = cls(int(split(_url,"/discuss/","/",True)),client_or_session)
        category.box_name = box_name
        category.name = _name.get_text(strip=True)
        _description:bs4.element.NavigableString|Any = _title.contents[-1]
        category.description = _description.string.strip()
        return category

async def get_forum_categories(client_or_session:"HTTPClient|Session|None"=None) -> dict[str, list[ForumCategory]]:
    if TYPE_CHECKING:
        box:bs4.Tag|Any
        category:bs4.Tag|Any
    returns:dict[str,list[ForumCategory]] = {}
    async with temporary_httpclient(client_or_session) as client:
        response = await client.get("https://scratch.mit.edu/discuss/")
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        boxes:bs4.Tag|Any = soup.find("div",{"class":"blocktable"})
        for box in boxes.find_all("div",{"class":"box"}):
            _box_head:bs4.Tag|Any = box.find("h4")
            box_title = str(_box_head.contents[-1]).strip()
            returns[box_title] = []

            _box_body:bs4.Tag|Any = box.find("tbody")
            categories:list[bs4.Tag|Any] = _box_body.find_all("tr")
            for category in categories:
                returns[box_title].append(ForumCategory._create_from_home(box_title,category,client_or_session))
    return returns