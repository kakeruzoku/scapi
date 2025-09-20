from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Final, Sequence, TypedDict

from .base import _BaseSiteAPI
from ..utils.types import (
    NewsPayload,
    CommunityFeaturedPayload,
    CommunityFeaturedProjectPayload,
    CommunityFeaturedRemixProjectPayload
)
from ..utils.common import (
    UNKNOWN,
    UNKNOWN_TYPE,
    MAYBE_UNKNOWN,
    dt_from_isoformat,
    api_iterative,
)
from ..utils.common import get_client_and_session

from .user import User
from .studio import Studio
from .project import Project

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

    def __repr__(self) -> str:
        return f"<News id:{self.id} headline:{self.headline}>"

    def _update_from_data(self, data:NewsPayload):
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
        client_or_session:"HTTPClient|Session|None",
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
    client,_ = get_client_and_session(client_or_session)
    client_or_session = client_or_session or client
    async for _p in api_iterative(
        client,f"https://api.scratch.mit.edu/news",
        limit=limit,offset=offset
    ):
        yield News._create_from_data(_p["id"],_p,client_or_session or client)

class CommunityFeaturedResponse(TypedDict):
    featured_projects:list[Project]
    featured_studios:list[Studio]
    most_loved_projects:list[Project]
    most_remixed_projects:list[Project]
    newest_projects:list[Project]
    design_studio_projects:list[Project]
    design_studio:Studio|None

def _add_community_featured_project(
        client_or_session:"HTTPClient|Session",
        list_object:"list[Project]",
        payload:Sequence[CommunityFeaturedProjectPayload|CommunityFeaturedRemixProjectPayload]
    ):
    for data in payload:
        project = Project(data.get("id"),client_or_session)
        project.title = data.get("title")
        project.love_count = data.get("love_count")
        project.author = User(data.get("creator"),client_or_session)
        project.remix_count = data.get("remixers_count",UNKNOWN)
        list_object.append(project)

async def get_community_featured(client_or_session:"HTTPClient|Session") -> CommunityFeaturedResponse:
    """
    コミュニティ特集を取得する。

    Args:
        client_or_session (HTTPClient|Session): 通信に使用するHTTPClientか、セッション

    Returns:
        CommunityFeaturedResponse:
    """
    client,_ = get_client_and_session(client_or_session)

    response = await client.get("https://api.scratch.mit.edu/proxy/featured")
    data:CommunityFeaturedPayload = response.json()

    _return:CommunityFeaturedResponse = {
        "featured_projects":[],
        "featured_studios":[],
        "most_loved_projects":[],
        "most_remixed_projects":[],
        "newest_projects":[],
        "design_studio_projects":[],
        "design_studio":None
    }
    for _data in data.get("community_featured_studios"):
        studio = Studio(_data.get("id"),client_or_session)
        studio.title = _data.get("title",UNKNOWN)
        _return["featured_studios"].append(studio)

    _add_community_featured_project(client_or_session,_return["featured_projects"],data.get("community_featured_projects"))
    _add_community_featured_project(client_or_session,_return["most_loved_projects"],data.get("community_most_loved_projects"))
    _add_community_featured_project(client_or_session,_return["most_remixed_projects"],data.get("community_most_remixed_projects"))
    _add_community_featured_project(client_or_session,_return["newest_projects"],data.get("community_newest_projects"))
    _add_community_featured_project(client_or_session,_return["design_studio_projects"],data.get("scratch_design_studio"))

    if data.get("scratch_design_studio"):
        _payload = data.get("scratch_design_studio")[0]
        _return["design_studio"] = Studio(_payload.get("gallery_id"))
        _return["design_studio"].title = _payload.get("gallery_title")

    return _return