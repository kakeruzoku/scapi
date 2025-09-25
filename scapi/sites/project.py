from __future__ import annotations

import datetime
import json
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final, Literal

import aiohttp
import bs4

from ..utils.types import (
    ProjectPayload,
    ProjectLovePayload,
    ProjectFavoritePayload,
    ProjectVisibilityPayload,
    UserFeaturedPayload,
    OldProjectPayload,
    OldProjectEditPayload,
    ReportPayload,
    RemixTreePayload,
    RemixTreeDatetimePayload,
    search_mode,
    explore_query
)
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    UNKNOWN_TYPE,
    api_iterative,
    dt_from_isoformat,
    dt_from_timestamp,
    _AwaitableContextManager,
    Tag,
    split
)
from ..utils.client import HTTPClient
from ..utils.error import (
    NoDataError,
    TooManyRequests,
    InvalidData,
    NotFound
)
from ..utils.file import (
    File,
    _file
)
from ..event.cloud import ScratchCloud
from ..event.comment import CommentEvent

from .base import _BaseSiteAPI
from .comment import (
    Comment,
    get_comment_from_old
)
from .activity import (
    CloudActivity
)

if TYPE_CHECKING:
    from .session import Session
    from .user import (
        User,
        ProjectFeaturedLabel
    )
    from .studio import Studio

class Project(_BaseSiteAPI[int]):
    """
    プロジェクトを表す

    Attributes:
        id (int): プロジェクトのID
        title (MAYBE_UNKNOWN[str]): プロジェクトのタイトル
        author (MAYBE_UNKNOWN[User]): プロジェクトの作者
        instructions (MAYBE_UNKNOWN[str]): プロジェクトの使い方欄
        description (MAYBE_UNKNOWN[str]): プロジェクトのメモとクレジット欄
        public (MAYBE_UNKNOWN[bool]): プロジェクトが公開されているか
        comments_allowed (MAYBE_UNKNOWN[bool]): コメント欄が開いているか
        deleted (MAYBE_UNKNOWN[bool]): プロジェクトがゴミ箱またはゴミ箱からも削除されているか。

        view_count (MAYBE_UNKNOWN[int]): プロジェクトの閲覧数
        love_count (MAYBE_UNKNOWN[int]): プロジェクトの「好き」の数
        favorite_count (MAYBE_UNKNOWN[int]): プロジェクトの「お気に入り」の数
        remix_count (MAYBE_UNKNOWN[int]): プロジェクトの「リミックス」の数

    .. warning::
        remix_count の値は 3.0APIのリスト形式での取得など(傾向等)では常に0になります。正確な値を確認したい場合は .update() を実行してください。
    
    Attributes:
        remix_parent_id (MAYBE_UNKNOWN[int|None]): プロジェクトの親プロジェクトID
        remix_root_id (MAYBE_UNKNOWN[int|None]): プロジェクトの元プロジェクトID

        comment_count (MAYBE_UNKNOWN[int|None]): コメントの数。Session.get_mystuff_projects()からでのみ取得できます。
    """
    def __repr__(self) -> str:
        return f"<Project id:{self.id} author:{self.author} session:{self.session}>"

    def __init__(self,id:int,client_or_session:"HTTPClient|Session|None"=None):
        super().__init__(client_or_session)
        self.id:Final[int] = id
        self.title:MAYBE_UNKNOWN[str] = UNKNOWN

        self.author:"MAYBE_UNKNOWN[User]" = UNKNOWN
        self.instructions:MAYBE_UNKNOWN[str] = UNKNOWN
        self.description:MAYBE_UNKNOWN[str] = UNKNOWN
        self.public:MAYBE_UNKNOWN[bool] = UNKNOWN
        self.comments_allowed:MAYBE_UNKNOWN[bool] = UNKNOWN
        self.deleted:MAYBE_UNKNOWN[bool] = UNKNOWN
        
        self._created_at:MAYBE_UNKNOWN[str] = UNKNOWN
        self._modified_at:MAYBE_UNKNOWN[str|None] = UNKNOWN
        self._shared_at:MAYBE_UNKNOWN[str|None] = UNKNOWN

        self.view_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.love_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.favorite_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.remix_count:MAYBE_UNKNOWN[int] = UNKNOWN

        self.remix_parent_id:MAYBE_UNKNOWN[int|None] = UNKNOWN
        self.remix_root_id:MAYBE_UNKNOWN[int|None] = UNKNOWN

        self.comment_count:MAYBE_UNKNOWN[int|None] = UNKNOWN
    
    async def update(self):
        response = await self.client.get(f"https://api.scratch.mit.edu/projects/{self.id}")
        self._update_from_data(response.json())

    def _update_from_data(self, data:ProjectPayload):
        self._update_to_attributes(
            title=data.get("title"),
            instructions=data.get("instructions"),
            description=data.get("description"),
            public=data.get("public"),
            comments_allowed=data.get("comments_allowed"),
            deleted=(data.get("visibility") == "notvisible")
        )
        
        _author = data.get("author")
        if _author:
            if self.author is UNKNOWN:
                from .user import User
                self.author = User(_author.get("username"),self.client_or_session)
            self.author._update_from_data(_author)
            

        _history = data.get("history")
        if _history:
            self._update_to_attributes(
                _created_at=_history.get("created"),
                _modified_at=_history.get("modified"),
                _shared_at=_history.get("shared")
            )

        _stats = data.get("stats")
        if _stats:
            self._update_to_attributes(
                view_count=_stats.get("views"),
                love_count=_stats.get("loves"),
                favorite_count=_stats.get("favorites"),
                remix_count=_stats.get("remixes")
            )

        _remix = data.get("remix")
        if _remix:
            self._update_to_attributes(
                remix_parent_id=_remix.get("parent"),
                remix_root_id=_remix.get("root")
            )

    def _update_from_old_data(self, data:OldProjectPayload):
        _author = data.get("creator")

        if _author:
            if self.author is UNKNOWN:
                from .user import User
                self.author = User(_author.get("username"),self.client_or_session)
            self.author._update_from_old_data(_author)

        self._update_to_attributes(
            title=data.get("title"),
            public=data.get("isPublished"),
            deleted=(data.get("visibility") == "trshbyusr"),

            _created_at=data.get("datetime_created"),
            _modified_at=data.get("datetime_modified"),
            _shared_at=data.get("datetime_shared"),

            view_count=data.get("view_count"),
            favorite_count=data.get("favorite_count"),
            remix_count=data.get("remixers_count"),
            love_count=data.get("love_count")
        )

    @staticmethod
    def _get_time_from_remixtree(data:MAYBE_UNKNOWN[RemixTreeDatetimePayload|None]) -> str|UNKNOWN_TYPE:
        if data is UNKNOWN: return UNKNOWN
        if data is None: return UNKNOWN
        dt = data.get("$date")
        if dt is UNKNOWN: return UNKNOWN
        return str(dt_from_timestamp(dt/1000))

    def _update_from_remixtree(self, data:RemixTreePayload):
        self._update_to_attributes(
            title=data.get("title"),
            deleted=(data.get("visibility") == "notvisible"),
            public=data.get("is_published"),

            _created_at=self._get_time_from_remixtree(data.get("datetime_created")),
            _modified_at=self._get_time_from_remixtree(data.get("datetime_modified") or data.get("mtime")),
            _shared_at=self._get_time_from_remixtree(data.get("datetime_shared")),

            favorite_count=data.get("favorite_count"),
            love_count=data.get("love_count"),

            remix_parent_id=data.get("parent_id")
        )

    @classmethod
    def _create_from_html(cls, data:bs4.Tag, client_or_session:"HTTPClient|Session"):
        from .user import User
        _a:Tag = data.find("a")
        id = int(split(str(_a["href"]),"projects/","/",True))
        project = cls(id,client_or_session)
        _title_span:Tag = data.find("span",{"class":"title"})
        _title_a:Tag = _title_span.find("a")
        project.title = _title_a.get_text()
        _author_span:Tag = data.find("span",{"class":"owner"})
        _author_name:Tag = _author_span.find("a")
        project.author = User(_author_name.get_text(),client_or_session)
        return project

    @property
    def _author_username(self) -> str:
        if not (self.author and self.author.username):
            raise NoDataError(self)
        return self.author.username
    
    @property
    def created_at(self) -> datetime.datetime|UNKNOWN_TYPE:
        """
        プロジェクトが作成された時間を返す

        Returns:
            datetime.datetime|UNKNOWN_TYPE: データがある場合、その時間。
        """
        return dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self) -> datetime.datetime|UNKNOWN_TYPE|None:
        """
        プロジェクトが最後に編集された時間を返す

        Returns:
            datetime.datetime|UNKNOWN_TYPE|None: データがある場合、その時間。
        """
        return dt_from_isoformat(self._modified_at)
    
    @property
    def shared_at(self) -> datetime.datetime|UNKNOWN_TYPE|None:
        """
        プロジェクトが共有された時間を返す

        Returns:
            datetime.datetime|UNKNOWN_TYPE|None: データがある場合、その時間。
        """
        return dt_from_isoformat(self._shared_at)
    
    @property
    def url(self) -> str:
        """
        プロジェクトのURLを取得する

        Returns:
            str:
        """
        return f"https://scratch.mit.edu/projects/{self.id}"
    
    async def get_remixes(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Project", None]:
        """
        リミックスされたプロジェクトを取得する。

        Args:
            limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
            offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。

        Yields:
            Project: リミックスされたプロジェクト
        """
        async for _p in api_iterative(
            self.client,f"https://api.scratch.mit.edu/projects/{self.id}/remixes",
            limit=limit,offset=offset
        ):
            yield Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_studios(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Studio", None]:
        """
        プロジェクトが追加されたスタジオを取得する。

        Args:
            limit (int|None, optional): 取得するスタジオの数。初期値は40です。
            offset (int|None, optional): 取得するスタジオの開始位置。初期値は0です。

        Yields:
            Studio: 追加されたスタジオ。
        """
        from .studio import Studio
        async for _s in api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self._author_username}/projects/{self.id}/studios",
            limit=limit,offset=offset
        ):
            yield Studio._create_from_data(_s["id"],_s,self.client_or_session)

    async def get_parent_project(self) -> "Project|None|UNKNOWN_TYPE":
        """
        プロジェクトの親プロジェクトを取得する。

        Raises:
            error.NotFound: プロジェクトが見つからない

        Returns:
            Project|None|UNKNOWN_TYPE: データが存在する場合、そのプロジェクト。
        """
        if isinstance(self.remix_parent_id,int):
            return await self._create_from_api(self.remix_parent_id,self.client_or_session)
        return self.remix_parent_id
        
    async def get_root_project(self) -> "Project|None|UNKNOWN_TYPE":
        """
        プロジェクトの元プロジェクトを取得する。

        Raises:
            error.NotFound: プロジェクトが見つからない

        Returns:
            Project|None|UNKNOWN_TYPE: データが存在する場合、そのプロジェクト。
        """
        if isinstance(self.remix_root_id,int):
            return await self._create_from_api(self.remix_root_id,self.client_or_session)
        return self.remix_root_id
        
    async def get_comments(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Comment", None]:
        """
        プロジェクトに投稿されたコメントを取得する。

        Args:
            limit (int|None, optional): 取得するコメントの数。初期値は40です。
            offset (int|None, optional): 取得するコメントの開始位置。初期値は0です。

        Yields:
            Comment: プロジェクトに投稿されたコメント
        """
        async for _c in api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self._author_username}/projects/{self.id}/comments",
            limit=limit,offset=offset
        ):
            yield Comment._create_from_data(_c["id"],_c,place=self)

    async def get_comment_by_id(self,comment_id:int) -> "Comment":
        """
        コメントIDからコメントを取得する。

        Args:
            comment_id (int): 取得したいコメントのID

        Raises:
            error.NotFound: コメントが見つからない
        
        Returns:
            Comment: 見つかったコメント
        """
        return await Comment._create_from_api(comment_id,place=self)
    
    def get_comments_from_old(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator["Comment", None]:
        """
        プロジェクトに投稿されたコメントを古いAPIから取得する。

        Args:
            start_page (int|None, optional): 取得するコメントの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するコメントの終了ページ位置。初期値はstart_pageの値です。

        Returns:
            Comment: プロジェクトに投稿されたコメント
        """
        return get_comment_from_old(self,start_page,end_page)
    
    def comment_event(self,interval:int=30,is_old:bool=False) -> CommentEvent:
        """
        コメントイベントを作成する。

        Args:
            interval (int, optional): コメントの更新間隔。デフォルトは30秒です。
            is_old (bool, optional): 古いAPIから取得するか。デフォルトはFalseです。

        Returns:
            CommentEvent:
        """
        return CommentEvent(self,interval,is_old)
        
    async def get_cloud_logs(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["CloudActivity", None]:
        """
        クラウド変数のログを取得する。

        Args:
            limit (int|None, optional): 取得するログの数。初期値は100です。
            offset (int|None, optional): 取得するログの開始位置。初期値は0です。

        Yields:
            CloudActivity
        """
        async for _a in api_iterative(
            self.client,"https://clouddata.scratch.mit.edu/logs",
            limit=limit,offset=offset,max_limit=100,params={"projectid":self.id},
        ):
            yield CloudActivity._create_from_log(_a,self.id,self.client_or_session)


    async def edit_project(
            self,project_data:File|dict|str|bytes,is_json:bool|None=None
        ):
        """
        プロジェクト本体を更新します。

        Args:
            project_data (File | dict | str | bytes): プロジェクトのデータ本体。
            is_json (bool | None, optional): プロジェクトのデータの形式。zip形式を使用したい場合はFalseを指定してください。Noneにすると簡易的に判定されます。
        """

        if isinstance(project_data,dict):
            project_data = json.dumps(project_data)
        if isinstance(project_data,(bytes, bytearray, memoryview)):
            is_json = False
        elif isinstance(project_data,str):
            is_json = True

        async with _file(project_data) as f:
            self.require_session()
            content_type = "application/json" if is_json else "application/zip"
            headers = self.client.scratch_headers | {"Content-Type": content_type}
            await self.client.put(
                f"https://projects.scratch.mit.edu/{self.id}",
                data=f.fp,headers=headers
            )

    async def edit(
            self,*,
            comment_allowed:bool|None=None,
            title:str|None=None,
            instructions:str|None=None,
            description:str|None=None,
        ):
        """
        プロジェクトのステータスを編集します。

        Args:
            comment_allowed (bool | None, optional): コメントを許可するか
            title (str | None, optional): プロジェクトのタイトル
            instructions (str | None, optional): プロジェクトの「使い方」欄
            description (str | None, optional): プロジェクトの「メモとクレジット」欄
        """
        self.require_session()
        data = {}
        if comment_allowed is not None: data["comment_allowed"] = comment_allowed
        if title is not None: data["title"] = title
        if instructions is not None: data["instructions"] = instructions
        if description is not None: data["description"] = description

        r = await self.client.put(f"https://api.scratch.mit.edu/projects/{self.id}",json=data)
        self._update_from_data(r.json())
    
    async def old_edit(
            self,*,
            title:str|None=None,
            share:bool|None=None,
            trash:bool|None=None,
        ):
        """
        プロジェクトのステータスを古いAPIで編集します。

        Args:
            title (str | None, optional): プロジェクトのタイトル
            share (bool | None, optional): プロジェクトの共有状態
            trash (bool | None, optional): ゴミ箱に入れるか
        """
        self.require_session()
        data = {}
        if share is not None: data["isPublished"] = share
        if title is not None: data["title"] = title
        if trash is not None: data["visibility"] = "trshbyusr" if trash else "visible"
        r = await self.client.put(f"https://scratch.mit.edu/site-api/projects/all/{self.id}/",json=data)
        _data:OldProjectEditPayload = r.json()
        self._update_to_attributes(
            title=_data.get("title"),
            _modified_at=_data.get("datetime_modified")
        )

    async def set_thumbnail(self,thumbnail:File|bytes):
        """
        プロジェクトのサムネイルを変更します。

        Args:
            thumbnail (File | bytes): サムネイルデータ
        """
        self.require_session()
        async with _file(thumbnail) as f:
            await self.client.post(
                f"https://scratch.mit.edu/internalapi/project/thumbnail/{self.id}/set/",
                data=f.fp
            )

    async def share(self):
        """
        プロジェクトを共有する
        """
        self.require_session()
        await self.client.put(f"https://api.scratch.mit.edu/proxy/projects/{self.id}/share")
        self.public = True

    async def unshare(self):
        """
        プロジェクトを非共有にする
        """
        self.require_session()
        await self.client.put(f"https://api.scratch.mit.edu/proxy/projects/{self.id}/unshare")
        self.public = False

    async def get_visibility(self) -> "ProjectVisibility":
        """
        プロジェクトのステータスを取得します。

        Returns:
            ProjectVisibility: プロジェクトの共有ステータス
        """
        self.require_session()
        response = await self.client.get(f"https://api.scratch.mit.edu/users/{self._session.username}/projects/{self.id}/visibility")
        return ProjectVisibility(response.json(),self)


    async def create_remix(self,title:str|None=None) -> "Project":
        """
        プロジェクトのリミックスを作成します。
        プロジェクトの中身は複製されません。

        Args:
            title (str | None, optional): プロジェクトのタイトル。

        Returns:
            Project: 作成されたプロジェクト
        """
        #TODO download project
        self.require_session()
        return await self._session.create_project(title,remix_id=self.id)
    
    async def is_loved(self) -> bool:
        """
        プロジェクトに「好き」を付けているかを取得します。

        Returns:
            bool: プロジェクトに「好き」を付けているか
        """
        self.require_session()
        response = await self.client.get(f"https://api.scratch.mit.edu/projects/{self.id}/loves/user/{self._session.username}")
        data:ProjectLovePayload = response.json()
        return data.get("userLove")

    async def add_love(self) -> bool:
        """
        プロジェクトに「好き」を付けます。

        Returns:
            bool: ステータスが変更されたか
        """
        self.require_session()
        response = await self.client.post(f"https://api.scratch.mit.edu/projects/{self.id}/loves/user/{self._session.username}")
        data:ProjectLovePayload = response.json()
        return data.get("statusChanged")
    
    async def remove_love(self) -> bool:
        """
        プロジェクトから「好き」を外します。

        Returns:
            bool: ステータスが変更されたか
        """
        self.require_session()
        response = await self.client.delete(f"https://api.scratch.mit.edu/projects/{self.id}/loves/user/{self._session.username}")
        data:ProjectLovePayload = response.json()
        return data.get("statusChanged")
    
    async def is_favorited(self) -> bool:
        """
        プロジェクトに「お気に入り」を付けているかを取得します。

        Returns:
            bool: プロジェクトに「お気に入り」を付けているか
        """
        self.require_session()
        response = await self.client.get(f"https://api.scratch.mit.edu/projects/{self.id}/favorites/user/{self._session.username}")
        data:ProjectFavoritePayload = response.json()
        return data.get("userFavorite")

    async def add_favorite(self) -> bool:
        """
        プロジェクトに「お気に入り」を付けます。

        Returns:
            bool: ステータスが変更されたか
        """
        self.require_session()
        response = await self.client.post(f"https://api.scratch.mit.edu/projects/{self.id}/favorites/user/{self._session.username}")
        data:ProjectFavoritePayload = response.json()
        return data.get("statusChanged")
    
    async def remove_favorite(self) -> bool:
        """
        プロジェクトから「お気に入り」を外します。

        Returns:
            bool: ステータスが変更されたか
        """
        self.require_session()
        response = await self.client.delete(f"https://api.scratch.mit.edu/projects/{self.id}/favorites/user/{self._session.username}")
        data:ProjectFavoritePayload = response.json()
        return data.get("statusChanged")
    
    async def add_view(self) -> bool:
        """
        プロジェクトの閲覧数を増やします。

        Returns:
            bool: 閲覧数が増えたか
        """
        try:
            await self.client.post(f"https://api.scratch.mit.edu/users/{self._author_username}/projects/{self.id}/views/")
        except TooManyRequests:
            return False
        else:
            return True
    
    async def post_comment(
        self,content:str,
        parent:"Comment|int|None"=None,commentee:"User|int|None"=None,
        is_old:bool=False
    ) -> "Comment":
        """
        コメントを投稿する。

        Args:
            content (str): コメントの内容
            parent (Comment|int|None, optional): 返信する場合、返信元のコメントかID
            commentee (User|int|None, optional): メンションする場合、ユーザーかそのユーザーのID
            is_old (bool, optional): 古いAPIを使用して送信するか

        Returns:
            Comment: 投稿されたコメント
        """
        return await Comment.post_comment(self,content,parent,commentee,is_old)

    def cloud(
            self,
            *,
            timeout:aiohttp.ClientWSTimeout|None=None,
            send_timeout:float|None=None
        ) -> ScratchCloud:
        return self._session.cloud(self.id,timeout=timeout,send_timeout=send_timeout)
    
    async def report(self,category:int,message:str) -> str:
        """
        プロジェクトを報告する。

        Args:
            category (int): 報告のカテゴリー
            message (str): 追加のメッセージ

        Returns:
            str: このプロジェクトのステータス
        """
        response = await self.client.post(
            f"https://api.scratch.mit.edu/proxy/projects/{self.id}/report",
            json={
                "notes":message,
                "report_category":str(category),
                "thumbnail":""
            }
        )
        data:ReportPayload|Literal[""] = response.json_or_text()
        if data == "":
            raise InvalidData(response)
        if not data.get("success"):
            raise InvalidData(response)
        return data.get("moderation_status")
    
    async def get_remixtree(self) -> RemixTree:
        response = await self.client.get(f"https://scratch.mit.edu/projects/{self.id}/remixtree/bare/")
        data:dict[str,RemixTreePayload]|str = response.json_or_text()
        if isinstance(data,str):
            raise NotFound(response)
        _all_remixtree:dict[int,"RemixTree"] = {}
        client_or_session = self.client_or_session

        root_id = int(data.pop("root_id")) # pyright: ignore[reportArgumentType]
        for k,v in data.items():
            k = int(k)
            project = self if k == self.id else None
            v["id"] = k
            remixtree = RemixTree(v,client_or_session,project=project)
            remixtree.root_id = root_id
            remixtree.project.remix_root_id = root_id
            _all_remixtree[k] = remixtree
        
        for r in _all_remixtree.values():
            r._all_remixtree = _all_remixtree

        return _all_remixtree[self.id]

class ProjectVisibility:
    """
    プロジェクトのステータス。

    Attributes:
        id (int): プロジェクトのID
        project (Project): ステータスを表しているプロジェクト
        author (User): そのプロジェクトの作者

        deleted (bool)
        censored (bool)
        censored_by_admin (bool)
        censored_by_community (bool)
        reshareble (bool)
        message (str)
    """
    def __init__(self,data:ProjectVisibilityPayload,project:Project):
        assert project.session
        self.id = data.get("projectId")
        self.project = project
        self.author = self.project.author or project.session.user
        self.author.id = data.get("creatorId")

        self.deleted = data.get("deleted")
        self.censored = data.get("censored")
        self.censored_by_admin = data.get("censoredByAdmin")
        self.censored_by_community = data.get("censoredByCommunity")
        self.reshareble = data.get("reshareable")
        self.message = data.get("message")

class ProjectFeatured:
    """
    注目のプロジェクト欄を表す。

    Attributes:
        project (Project): 設定されているプロジェクト
        author (User): そのプロジェクトの作者
        label (ProjectFeaturedLabel): プロジェクトのラベル
    """
    def __repr__(self):
        return repr(self.project)

    def __new__(cls,data:UserFeaturedPayload,user:"User"):
        _project_payload = data.get("featured_project_data")
        if _project_payload is None:
            return
        else:
            return super().__new__(cls)

    def __init__(self,data:UserFeaturedPayload,user:"User"):
        from .user import ProjectFeaturedLabel
        _project_payload = data.get("featured_project_data")
        _user_payload = data.get("user")
        assert _project_payload

        self.project = Project(int(_project_payload.get("id")),user.client_or_session)
        self.project._modified_at = _project_payload.get("datetime_modified") + "Z"
        self.project.title = _project_payload.get("title")

        self.author = self.project.author = user
        self.author.id = data.get("id")
        self.author.profile_id = _user_payload.get("pk")

        self.label:ProjectFeaturedLabel = ProjectFeaturedLabel.get_from_id(data.get("featured_project_label_id"))

class RemixTree(_BaseSiteAPI):
    """
    プロジェクトのリミックスツリーを表す

    Attributes:
        id (int): プロジェクトのID
        project (Project): プロジェクトのProject
        moderation_status (str): プロジェクトのステータス
        root_id (int): この木の根プロジェクトのID
    """
    moderation_status:str
    _ctime:str
    _children:list[int]
    _all_remixtree:dict[int,"RemixTree"]
    root_id:int

    def __init__(
            self,
            data:RemixTreePayload,
            client_or_session:HTTPClient|Session|None,
            *,
            project:Project|None=None
        ) -> None:
        super().__init__(client_or_session)

        self.id:Final[int] = data["id"]
        self.project:Project = project or Project(data["id"],client_or_session)
        self._update_from_data(data)

    def _update_from_data(self, data:RemixTreePayload):
        if self.project.author is UNKNOWN:
            from .user import User
            self.project.author = User(data["username"],self.client_or_session)

        self.project._update_from_remixtree(data)

        self._update_to_attributes(
            moderation_status=data.get("moderation_status"),
            _ctime=self.project._get_time_from_remixtree(data.get("ctime")),
            _children=data.get("children")
        )

    @property
    def parent(self) -> "RemixTree|None":
        """
        プロジェクトの親プロジェクトのRemixTree

        Returns:
            RemixTree|None:
        """
        parent_id = self.project.remix_parent_id
        if parent_id is UNKNOWN: raise ValueError()
        if parent_id is None: return
        return self._all_remixtree[parent_id]
    
    @property
    def root(self) -> "RemixTree":
        """
        プロジェクトの根プロジェクトのRemixTree

        Returns:
            RemixTree:
        """
        return self._all_remixtree[self.root_id]
    
    @property
    def children(self) -> list[RemixTree]:
        """
        このプロジェクトの子プロジェクトのRemixTree

        Returns:
            list[RemixTree]:
        """
        children:list["RemixTree"] = []
        for i in self._children:
            remixtree = self._all_remixtree.get(i)
            if remixtree is not None:
                children.append(remixtree)
        return children
    
    @property
    def all_remixtree(self)  -> list["RemixTree"]:
        """
        このプロジェクトのリミックスツリーに関連付けられている全てのRemixTree

        Returns:
            list[RemixTree]:
        """
        return list(self._all_remixtree.values())

def get_project(project_id:int,*,_client:HTTPClient|None=None) -> _AwaitableContextManager[Project]:
    """
    プロジェクトを取得する。

    Args:
        project_id (int): 取得したいプロジェクトのID

    Returns:
        _AwaitableContextManager[Project]: await か async with で取得できるプロジェクト
    """
    return _AwaitableContextManager(Project._create_from_api(project_id,_client))

async def explore_projects(
        client:HTTPClient,
        query:explore_query="*",
        mode:search_mode="trending",
        language:str="en",
        limit:int|None=None,
        offset:int|None=None,
        *,
        session:Session|None=None
    ) -> AsyncGenerator[Project]:
    """
    プロジェクトの傾向を取得する

    Args:
        client (HTTPClient): 使用するHTTPClient
        query (explore_query, optional): 取得するする種類。デフォルトは"*"(all)です。
        mode (Literal["trending","popular"], optional): 取得するモード。デフォルトは"trending"です。
        language (str, optional): 取得する言語。デフォルトは"en"です。
        limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
        offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。
        session (Session | None, optional): セッションを使用したい場合、使用したいセッション

    Yields:
        Project:
    """
    client_or_session = session or client
    async for _p in api_iterative(
        client,"https://api.scratch.mit.edu/explore/projects",limit,offset,
        params={"language":language,"mode":mode,"q":query}
    ):
        yield Project._create_from_data(_p["id"],_p,client_or_session)

async def search_projects(
        client:HTTPClient,
        query:str,
        mode:search_mode="trending",
        language:str="en",
        limit:int|None=None,
        offset:int|None=None,
        *,
        session:Session|None=None
    )-> AsyncGenerator[Project]:
    """
    プロジェクトを検索する

    Args:
        client (HTTPClient): 使用するHTTPClient
        query (str): 検索したい内容
        mode (Literal["trending","popular"], optional): 取得するモード。デフォルトは"trending"です。
        language (str, optional): 取得する言語。デフォルトは"en"です。
        limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
        offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。
        session (Session | None, optional): セッションを使用したい場合、使用したいセッション

    Yields:
        Project:
    """
    client_or_session = session or client
    async for _p in api_iterative(
        client,"https://api.scratch.mit.edu/search/projects",limit,offset,
        params={"language":language,"mode":mode,"q":query}
    ):
        yield Project._create_from_data(_p["id"],_p,client_or_session)