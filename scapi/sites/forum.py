from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final
import math

import aiohttp
import bs4

from scapi.sites.session import Session
from ..utils.client import HTTPClient
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    _AwaitableContextManager,
    temporary_httpclient,
    split,
    Tag
)

from .base import _BaseSiteAPI
from .user import User

if TYPE_CHECKING:
    from .session import Session

"""
TODO
- ForumPostの実装
- 検索とか
- 投稿とかのユーザーアクション
"""

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
        self.page_count:MAYBE_UNKNOWN[int] = UNKNOWN

        self.box_name:MAYBE_UNKNOWN[str] = UNKNOWN
        self.description:MAYBE_UNKNOWN[str] = UNKNOWN
        self.topic_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.post_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.last_post:MAYBE_UNKNOWN[ForumPost] = UNKNOWN

    def __repr__(self) -> str:
        return f"<ForumCategory id:{self.id} name:{self.name}>"

    @classmethod
    def _create_from_home(
        cls,
        box_name:str,
        data:bs4.Tag,
        client_or_session:"HTTPClient|Session|None"=None
    ):
        _title:Tag = data.find("div",{"class":"tclcon"})
        _name:Tag = _title.find("a")
        _url:str|Any = _name["href"]

        category = cls(int(split(_url,"/discuss/","/",True)),client_or_session)
        category.box_name = box_name
        category.name = _name.get_text(strip=True)
        _description:bs4.element.NavigableString|Any = _title.contents[-1]
        category.description = _description.string.strip()
        
        _topic_count:Tag = data.find("td",{"class":"tc2"})
        category.topic_count = int(_topic_count.get_text())
        _post_count:Tag = data.find("td",{"class":"tc3"})
        category.post_count = int(_post_count.get_text())
        category.page_count = math.ceil(category.post_count / 25)
        category.last_post = load_last_post(category,data)

        return category
    
    async def update(self):
        response = await self.client.get(f"https://scratch.mit.edu/discuss/{self.id}/")
        self._update_from_data(bs4.BeautifulSoup(response.text, "html.parser"))

    def _update_from_data(self,data:Tag):
        _main_block:Tag = data.find("div",{"id":"vf"})
        _head:Tag = _main_block.find("div",{"class":"box-head"})
        _name:Tag = _head.find("span")
        self.name = _name.get_text().strip()

        _pages:Tag = data.find("div",{"class":"pagination"})
        _page = _pages.select("span.current.page, a.page")[-1]
        self.page_count = int(_page.get_text())

    async def get_topics(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator["ForumTopic"]:
        if TYPE_CHECKING:
            _topic:Tag
        start_page = start_page or 1
        end_page = end_page or start_page
        is_first:bool = True
        for i in range(start_page,end_page+1):
            response = await self.client.get(f"https://scratch.mit.edu/discuss/{self.id}/",params={"page":i})
            data = bs4.BeautifulSoup(fix_html(response.text), "html.parser")
            empty_tag:Tag|None = data.find("td",{"class":"djangobbcon1"})
            if empty_tag is not None:
                return #empty
            if is_first:
                self._update_from_data(data)
                is_first = False
            _body:Tag = data.find("tbody")
            for _topic in _body.find_all("tr"):
                yield ForumTopic._create_from_category(self,_topic,self.client_or_session)

    
class ForumTopic(_BaseSiteAPI):
    """
    フォーラムのトピックを表す

    Attributes:
        id (int): トピックのID
        name (MAYBE_UNKNOWN[str]): トピックの名前
        category (MAYBE_UNKNOWN[ForumCategory]): トピックが属しているカテゴリー
        page_count (MAYBE_UNKNOWN[int]): ページの数

        is_unread (MAYBE_UNKNOWN[bool]): 未読の投稿があるか
        is_sticky (MAYBE_UNKNOWN[bool]): ピン留めされているか
        is_closed (MAYBE_UNKNOWN[bool]): 閉じられているか
        post_count (MAYBE_UNKNOWN[int]): 投稿されたポストの数
        view_count (MAYBE_UNKNOWN[int]): トピックが閲覧された回数
    """
    def __init__(self,id:int,client_or_session:"HTTPClient|Session|None"=None):
        super().__init__(client_or_session)
        self.id:Final[int] = id
        self.name:MAYBE_UNKNOWN[str] = UNKNOWN
        self.category:MAYBE_UNKNOWN[ForumCategory] = UNKNOWN
        self.page_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.author:MAYBE_UNKNOWN[User] = UNKNOWN

        self.is_unread:MAYBE_UNKNOWN[bool] = UNKNOWN
        self.is_sticky:MAYBE_UNKNOWN[bool] = UNKNOWN
        self.is_closed:MAYBE_UNKNOWN[bool] = UNKNOWN
        self.post_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.view_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.last_post:MAYBE_UNKNOWN[ForumPost] = UNKNOWN

    @classmethod
    def _create_from_category(
        cls,
        category:ForumCategory,
        data:bs4.Tag,
        client_or_session:"HTTPClient|Session|None"=None
    ):
        _tcl:Tag = data.find("td",{"class":"tcl"})
        _h3:Tag = _tcl.find("h3")
        _a:Tag = _h3.find("a")
        _url:str|Any = _a["href"]

        topic = cls(int(split(_url,"/discuss/topic/","/",True)),client_or_session)
        topic.category = category
        topic.name = _a.get_text(strip=True)
        topic.is_unread = _h3.get("class") is None

        _post_count:Tag = data.find("td",{"class":"tc2"})
        topic.post_count = int(_post_count.get_text())
        topic.page_count = math.ceil(topic.post_count / 20)
        _view_count:Tag = data.find("td",{"class":"tc3"})
        topic.view_count = int(_view_count.get_text())

        _user:Tag = _tcl.find("span",{"class":"byuser"})
        topic.author = User(_user.get_text(strip=True).removeprefix("by "),client_or_session)

        if _tcl.find("div",{"class":"forumicon"}) is not None:
            topic.is_closed, topic.is_sticky = False,False
        elif _tcl.find("div",{"class":"iclosed"}) is not None:
            topic.is_closed, topic.is_sticky = True,False
        elif _tcl.find("div",{"class":"isticky"}) is not None:
            topic.is_closed, topic.is_sticky = False,True
        elif _tcl.find("div",{"class":"isticky iclosed"}) is not None:
            topic.is_closed, topic.is_sticky = True,True

        topic.last_post = load_last_post(topic,data)

        return topic
    
    async def update(self):
        response = await self.client.get(f"https://scratch.mit.edu/discuss/topic/{self.id}/")
        self._update_from_data(bs4.BeautifulSoup(response.text, "html.parser"))

    def _update_from_data(self,data:Tag):
        self.is_unread = False
        _linkst:Tag = data.find("div",{"class":"linkst"})
        _place:Tag = _linkst.find("ul")
        _places:bs4.ResultSet[Tag] = _place.find_all("li")
        
        _category_a:Tag = _places[1].find("a")
        if self.category is UNKNOWN:
            self.category = ForumCategory(int(split(str(_category_a["href"]),"/discuss/","/",True)),self.client_or_session)
        self.category.name = _category_a.get_text()

        self.name = str(_places[2].next_element).removeprefix("»").strip()

        _pages:Tag = data.find("div",{"class":"pagination"})
        _page = _pages.select("span.current.page, a.page")[-1]
        self.page_count = int(_page.get_text())

    async def follow(self):
        """
        このトピックをフォローする
        """
        await self.client.post(f"https://scratch.mit.edu/discuss/subscription/topic/{self.id}/add/")

    async def unfollow(self):
        """
        このトピックのフォローを外す
        """
        await self.client.post(f"https://scratch.mit.edu/discuss/subscription/topic/{self.id}/remove/")

    async def get_posts(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator["ForumPost"]:
        start_page = start_page or 1
        end_page = end_page or start_page
        is_first:bool = True
        for i in range(start_page,end_page+1):
            response = await self.client.get(f"https://scratch.mit.edu/discuss/topic/{self.id}/",params={"page":i})
            data = bs4.BeautifulSoup(fix_html(response.text), "html.parser")
            not_empty_tag:Tag|None = data.find("div",{"class":"pagination"})
            if not_empty_tag is None:
                return #empty
            if is_first:
                self._update_from_data(data)
                is_first = False
            _posts:bs4.ResultSet[Tag] = data.find_all("div",{"class":"blockpost roweven firstpost"})
            for _post in _posts:
                id = int(str(_post["id"]).removeprefix("p"))
                yield ForumPost._create_from_data(id,_post,self.client_or_session)

class ForumPost(_BaseSiteAPI):
    def __init__(self,id:int,client_or_session:HTTPClient|Session|None) -> None:
        super().__init__(client_or_session)
        self.id:Final[int] = id

        self.number:MAYBE_UNKNOWN[int] = UNKNOWN
        self.author:MAYBE_UNKNOWN[User] = UNKNOWN
        self.created_at:MAYBE_UNKNOWN[datetime.datetime] = UNKNOWN
        self.modified_at:MAYBE_UNKNOWN[datetime.datetime|None] = UNKNOWN
        self.modified_by:MAYBE_UNKNOWN[User|None] = UNKNOWN
        self.content:MAYBE_UNKNOWN[bs4.Tag] = UNKNOWN

    def _update_from_data(self, data:bs4.Tag):
        pass

async def get_forum_categories(client_or_session:"HTTPClient|Session|None"=None) -> dict[str, list[ForumCategory]]:
    """
    フォーラムのカテゴリー一覧を取得する。

    Args:
        client_or_session (HTTPClient|Session|None, optional): 接続に使用するHTTPClientかSession

    Returns:
        dict[str, list[ForumCategory]]: ボックスの名前と、そこに属しているカテゴリーのペア
    """
    if TYPE_CHECKING:
        box:Tag
        category:Tag
    returns:dict[str,list[ForumCategory]] = {}
    async with temporary_httpclient(client_or_session) as client:
        response = await client.get("https://scratch.mit.edu/discuss/")
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        boxes:Tag = soup.find("div",{"class":"blocktable"})
        for box in boxes.find_all("div",{"class":"box"}):
            _box_head:Tag = box.find("h4")
            box_title = str(_box_head.contents[-1]).strip()
            returns[box_title] = []

            _box_body:Tag = box.find("tbody")
            categories:list[Tag] = _box_body.find_all("tr")
            for category in categories:
                returns[box_title].append(ForumCategory._create_from_home(box_title,category,client_or_session or client))
    return returns

month_dict = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

def decode_datetime(text:str) -> datetime.datetime:
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
        date = datetime.date(int(year),int(month),int(day))
    hour,minute,second = _time.split(":")
    time = datetime.time(int(hour),int(minute),int(second))
    return datetime.datetime.combine(date,time,datetime.timezone.utc)

def fix_html(text:str):
    "Remove html vandal /div tag"
    return text.replace(
        "<div class=\"nosize\"><!-- --></div>\n                                    </div>",
        "<div class=\"nosize\"><!-- --></div>"
    )

def load_last_post(self:_BaseSiteAPI,data:bs4.Tag) -> ForumPost:
    _last_post:Tag = data.find("td",{"class":"tcr"})
    _post:Tag = _last_post.find("a")
    _post_author:Tag = _last_post.find("span")
    _last_post_url:str|Any = _post["href"]
    
    post = ForumPost(int(split(_last_post_url,"/discuss/post/","/",True)),self.client_or_session)
    post.author = User(_post_author.get_text(strip=True).removeprefix("by "))
    post.created_at = decode_datetime(_post.get_text())
    return post