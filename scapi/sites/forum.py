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
    """
    フォーラムのカテゴリーを表す

    Attributes:
        id (int): カテゴリーのID
        name (MAYBE_UNKNOWN[str]): カテゴリーの名前

        box_name (MAYBE_UNKNOWN[str]): ボックスの名前
        description (MAYBE_UNKNOWN[str]): カテゴリーの説明
        topic_count (MAYBE_UNKNOWN[int]): トピックの数
        post_count (MAYBE_UNKNOWN[int]): 投稿の数
    """
    def __init__(self,id:int,client_or_session:"HTTPClient|Session|None"=None):
        super().__init__(client_or_session)
        self.id:Final[int] = id

        self.name:MAYBE_UNKNOWN[str] = UNKNOWN

        self.box_name:MAYBE_UNKNOWN[str] = UNKNOWN
        self.description:MAYBE_UNKNOWN[str] = UNKNOWN
        self.topic_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.post_count:MAYBE_UNKNOWN[int] = UNKNOWN
        #self.last_post:MAYBE_UNKNOWN

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
        
        _topic_count:bs4.Tag|Any = data.find("td",{"class":"tc2"})
        category.topic_count = int(_topic_count.get_text())
        _post_count:bs4.Tag|Any = data.find("td",{"class":"tc3"})
        category.post_count = int(_post_count.get_text())

        if False: #ForumPost実装したら
            _last_post:bs4.Tag|Any = data.find("td",{"class":"tcr"})
            _post:bs4.Tag|Any = _last_post.find("a")
            _post_author:bs4.Tag|Any = _last_post.find("span")
            last_post_username = _post_author.get_text(strip=True).removeprefix("by ")
            _last_post_url:str|Any = _post["href"]
            last_post_id = int(split(_last_post_url,"/discuss/post/","/",True))
            last_post_datetime = fix_datetime(_post.get_text())

        return category

async def get_forum_categories(client_or_session:"HTTPClient|Session|None"=None) -> dict[str, list[ForumCategory]]:
    """
    フォーラムのカテゴリー一覧を取得する。

    Args:
        client_or_session (HTTPClient|Session|None, optional): 接続に使用するHTTPClientかSession

    Returns:
        dict[str, list[ForumCategory]]: ボックスの名前と、そこに属しているカテゴリーのペア
    """
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

month_dict = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

def fix_datetime(text:str) -> datetime.datetime:
    text = text.strip()
    if text.startswith("Today"):
        date = datetime.date.today()
        _,_,_time = text.partition(" ")
    elif text.startswith("Yesterday"):
        date = datetime.date.today()-datetime.timedelta(days=1)
        _,_,_time = text.partition(" ")
    else:
        month = month_dict[text[:3]]
        _,_,text = text.partition(" ")
        day,_,text = text.partition(", ")
        year,_,_time = text.partition(" ")
        date = datetime.datetime(int(year),int(month),int(day))
    hour,minute,second = _time.split(":")
    time = datetime.time(int(hour),int(minute),int(second))
    return datetime.datetime.combine(date,time,datetime.timezone.utc)
