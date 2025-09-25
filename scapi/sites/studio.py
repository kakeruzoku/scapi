from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Final, Literal

import aiohttp
from ..utils.types import (
    StudioPayload,
    StudioRolePayload,
    OldStudioPayload,
    StudioClassroomPayload,
    ReportPayload,
    search_mode,
    explore_query
)
from ..utils.activity_types import StudioAnyActivity
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    UNKNOWN_TYPE,
    api_iterative,
    dt_from_isoformat,
    _AwaitableContextManager
)
from ..utils.client import HTTPClient
from ..utils.error import (
    ClientError,
    NotFound,
    InvalidData
)
from ..utils.file import (
    File,
    _read_file
)

from ..event.comment import CommentEvent

from .base import _BaseSiteAPI
from .comment import (
    Comment,
    get_comment_from_old
)
from .project import Project
from .activity import Activity

if TYPE_CHECKING:
    from .session import Session
    from .user import User
    from .classroom import Classroom

class Studio(_BaseSiteAPI[int]):
    """
    スタジオを表す

    Attributes:
        id (int): スタジオのID
        title (MAYBE_UNKNOWN[str]): スタジオの名前
        host_id (MAYBE_UNKNOWN[int]): スタジオの所有者のユーザーID
        description (MAYBE_UNKNOWN[str]): スタジオの説明欄
        open_to_all (MAYBE_UNKNOWN[bool]): 誰でもプロジェクトを追加できるか
        comments_allowed (MAYBE_UNKNOWN[bool]): コメント欄が開いているか

        comment_count (MAYBE_UNKNOWN[int]): コメントの数(<=100)
        follower_count (MAYBE_UNKNOWN[int]): フォロワーの数
        manager_count (MAYBE_UNKNOWN[int]): マネージャーの数
        project_count (MAYBE_UNKNOWN[int]): プロジェクトの数(<=100)

        _host (MAYBE_UNKNOWN[User]): 所有者の情報。Session.get_mystuff_studios()からでのみ取得できます。
    """
    def __repr__(self) -> str:
        return f"<Studio id:{self.id} session:{self.session}>"

    def __init__(self,id:int,client_or_session:"HTTPClient|Session|None"=None):
        super().__init__(client_or_session)
        self.id:Final[int] = id
        self.title:MAYBE_UNKNOWN[str] = UNKNOWN
        self.host_id:MAYBE_UNKNOWN[int] = UNKNOWN
        self.description:MAYBE_UNKNOWN[str] = UNKNOWN
        self.open_to_all:MAYBE_UNKNOWN[bool] = UNKNOWN
        self.comments_allowed:MAYBE_UNKNOWN[bool] = UNKNOWN

        self._created_at:MAYBE_UNKNOWN[str] = UNKNOWN
        self._modified_at:MAYBE_UNKNOWN[str] = UNKNOWN

        self.comment_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.follower_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.manager_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.project_count:MAYBE_UNKNOWN[int] = UNKNOWN

        self._host:MAYBE_UNKNOWN["User"] = UNKNOWN
    
    async def update(self):
        response = await self.client.get(f"https://api.scratch.mit.edu/studios/{self.id}")
        self._update_from_data(response.json())

    def _update_from_data(self, data:StudioPayload):
        self._update_to_attributes(
            title=data.get("title"),
            host_id=data.get("host"),
            description=data.get("description"),
            open_to_all=data.get("open_to_all"),
            comments_allowed=data.get("comments_allowed")
        )
        

        _history = data.get("history")
        if _history:
            self._update_to_attributes(
                _created_at=_history.get("created"),
                _modified_at=_history.get("modified"),
            )

        _stats = data.get("stats")
        if _stats:
            self._update_to_attributes(
                comment_count=_stats.get("comments"),
                follower_count=_stats.get("followers"),
                manager_count=_stats.get("managers"),
                project_count=_stats.get("projects")
            )

    def _update_from_old_data(self, data:OldStudioPayload):
        from .user import User
        _author = data.get("owner")

        if _author:
            if self._host is UNKNOWN:
                self._host = User(_author.get("username"),self.client_or_session)
            self._host._update_from_old_data(_author)
        
        self._update_to_attributes(
            title=data.get("title"),

            _created_at=data.get("datetime_created"),
            _modified_at=data.get("datetime_modified"),

            comment_count=data.get("commenters_count"),
            curator_count=data.get("curators_count"),
            project_count=data.get("projecters_count"),

            description=data.get("description")
        )
    
    @property
    def created_at(self) -> datetime.datetime|UNKNOWN_TYPE:
        """
        スタジオが作成された時間を返す

        Returns:
            datetime.datetime|UNKNOWN_TYPE: データがある場合、その時間。
        """
        return dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self) -> datetime.datetime|UNKNOWN_TYPE:
        """
        スタジオが最後に編集された時間を返す

        Returns:
            datetime.datetime|UNKNOWN_TYPE: データがある場合、その時間。
        """
        return dt_from_isoformat(self._modified_at)
    
    @property
    def url(self) -> str:
        """
        スタジオのURLを取得する

        Returns:
            str:
        """
        return f"https://scratch.mit.edu/studios/{self.id}"
    
    
    async def get_projects(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Project", None]:
        """
        スタジオに入れられているプロジェクトを取得する。

        Args:
            limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
            offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。

        Yields:
            Project: 取得したプロジェクト
        """
        async for _p in api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/projects",
            limit=limit,offset=offset
        ):
            yield Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_host(self) -> "User":
        """
        スタジオの所有者ユーザーを取得する。

        Returns:
            User: 取得したユーザー
        """
        return await anext(self.get_managers(limit=1))

    async def get_managers(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["User", None]:
        """
        スタジオのマネージャーを取得する。

        Args:
            limit (int|None, optional): 取得するユーザーの数。初期値は40です。
            offset (int|None, optional): 取得するユーザーの開始位置。初期値は0です。

        Yields:
            User: 取得したユーザー
        """
        from .user import User
        async for _u in api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/managers",
            limit=limit,offset=offset
        ):
            yield User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_curators(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["User", None]:
        """
        スタジオのキュレーターを取得する。

        Args:
            limit (int|None, optional): 取得するユーザーの数。初期値は40です。
            offset (int|None, optional): 取得するユーザーの開始位置。初期値は0です。

        Yields:
            User: 取得したユーザー
        """
        from .user import User
        async for _u in api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/curators",
            limit=limit,offset=offset
        ):
            yield User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_comments(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Comment", None]:
        """
        スタジオに投稿されたコメントを取得する。

        Args:
            limit (int|None, optional): 取得するコメントの数。初期値は40です。
            offset (int|None, optional): 取得するコメントの開始位置。初期値は0です。

        Yields:
            Comment: プロジェクトに投稿されたコメント
        """
        async for _c in api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/comments",
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
    
    def get_comments_from_old(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator["Comment", None]:
        """
        スタジオに投稿されたコメントを古いAPIから取得する。

        Args:
            start_page (int|None, optional): 取得するコメントの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するコメントの終了ページ位置。初期値はstart_pageの値です。

        Returns:
            Comment: 取得したコメント
        """
        return get_comment_from_old(self,start_page,end_page)
    
    async def get_classroom_id(self) -> int|None:
        """_
        スタジオが属しているクラスのIDを返す

        Returns:
            int|None:
        """
        try:
            response = await self.client.get(f"https://api.scratch.mit.edu/studios/{self.id}/classroom")
        except NotFound:
            return
        data:StudioClassroomPayload = response.json()
        return data.get("id")
    
    async def get_classroom(self) -> "Classroom|None":
        """_
        スタジオが属しているクラスを返す

        Returns:
            Classroom|None:
        """
        from .classroom import Classroom
        classroom_id = await self.get_classroom_id()
        if classroom_id is None:
            return
        return await Classroom._create_from_api(classroom_id,self.client_or_session)
    
    async def get_activities(self,limit:int|None=None,offset_dt:datetime.datetime|None=None) -> AsyncGenerator[Activity]:
        """
        スタジオのアクティビティを取得する。

        Args:
            limit (int | None, optional): 取得するアクティビティの数。初期値は40です。
            offset_dt (datetime.datetime | None, optional): 取得したい最初のアクティビティの時間

        Yields:
            Activity:
        """
        if offset_dt is not None:
            if offset_dt.tzinfo is None:
                offset_dt = offset_dt.replace(tzinfo=datetime.timezone.utc)
            else:
                offset_dt = offset_dt.astimezone(datetime.timezone.utc)
            
            offset:dict[str,str|int|float] = {"dateLimit":offset_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')}
        else:
            offset = {}

        limit = limit or 40
        for i in range(0,limit,40):
            response = await self.client.get(
                f"https://api.scratch.mit.edu/studios/{self.id}/activity/",
                params={"limit":min(40,limit-i)}|offset
            )
            data:list[StudioAnyActivity] = response.json()
            last = None
            for i in data:
                last = Activity._create_from_studio(i,self)
                yield last
            if not data:
                return
            created_at = last and last.created_at
            if created_at is None:
                return
            offset_dt = created_at+datetime.timedelta(seconds=1)
            offset = {"dateLimit":offset_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')}

    async def post_comment(
        self,content:str,
        parent:"Comment|int|None"=None,commentee:"User|int|None"=None,
        is_old:bool=False
    ) -> "Comment":
        """
        コメントを投稿します。

        Args:
            content (str): コメントの内容
            parent (Comment|int|None, optional): 返信する場合、返信元のコメントかID
            commentee (User|int|None, optional): メンションする場合、ユーザーかそのユーザーのID
            is_old (bool, optional): 古いAPIを使用して送信するか

        Returns:
            Comment: 投稿されたコメント
        """
        return await Comment.post_comment(self,content,parent,commentee,is_old)

    async def follow(self):
        """
        スタジオをフォローする。
        """
        self.require_session()
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/bookmarkers/{self.id}/add/",
            params={"usernames":self._session.username}
        )

    async def unfollow(self):
        """
        スタジオのフォローを解除する。
        """
        self.require_session()
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/bookmarkers/{self.id}/remove/",
            params={"usernames":self._session.username}
        )

    async def add_project(self,project:"Project|int"):
        """
        プロジェクトをスタジオに追加する。

        Args:
            project (Project|int): 追加するプロジェクトかそのID
        """
        self.require_session()
        project_id = project.id if isinstance(project,Project) else project
        await self.client.post(f"https://api.scratch.mit.edu/studios/{self.id}/project/{project_id}")

    async def remove_project(self,project:"Project|int"):
        """
        プロジェクトをスタジオから削除する。

        Args:
            project (Project|int): 削除するプロジェクトかそのID
        """
        self.require_session()
        project_id = project.id if isinstance(project,Project) else project
        await self.client.delete(f"https://api.scratch.mit.edu/studios/{self.id}/project/{project_id}")

    async def invite(self,user:"User|str"):
        """
        スタジオにユーザーを招待する

        Args:
            user (User|str): 招待したいユーザーかそのID
        """
        self.require_session()
        from .user import User
        username = user.username if isinstance(user,User) else user
        response = await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/invite_curator/",
            params={"usernames":username}
        )
        data = response.json()
        if data.get("status") != "success":
            raise ClientError(response,data.get("message"))
        
    async def accept_invite(self):
        """
        招待を受け取る
        """
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/add/",
            params={"usernames":self._session.username}
        )

    async def promote(self,user:"User|str"):
        """
        ユーザーをマネージャーに昇格する

        Args:
            user (User|str): 昇格したいユーザーかそのID
        """
        self.require_session()
        from .user import User
        username = user.username if isinstance(user,User) else user
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/promote/",
            params={"usernames":username}
        )
    
    async def remove_curator(self,user:"User|str"):
        """
        スタジオからユーザーを削除する。

        Args:
            user (User|str): 削除したいユーザーかそのID
        """
        self.require_session()
        from .user import User
        username = user.username if isinstance(user,User) else user
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/remove/",
            params={"usernames":username}
        )

    async def leave(self):
        """
        スタジオからぬける
        """
        await self.remove_curator(self._session.username)

    async def transfer_ownership(self,user:"str|User",password:str):
        """
        スタジオの所有権を移行する

        Args:
            user (str|User): 新たな所有者かそのユーザー名
            password (str): このアカウントのパスワード
        """
        self.require_session()
        from .user import User
        username = user.username if isinstance(user,User) else user
        await self.client.put(
            f"https://api.scratch.mit.edu/studios/{self.id}/transfer/{username}",
            json={"password":password}
        )

    async def get_my_role(self) -> "StudioStatus":
        """
        アカウントのスタジオでのステータスを取得する。

        Returns:
            StudioStatus: アカウントのステータス
        """
        self.require_session()
        response = await self.client.get(f"https://api.scratch.mit.edu/studios/{self.id}/users/{self._session.username}")
        return StudioStatus(response.json(),self)
    
    async def report(self,type:Literal["title","description","thumbnail"]) -> str:
        """
        スタジオを報告する

        Args:
            type (Literal["title","description","thumbnail"]): 報告の理由

        Returns:
            str: このスタジオのステータス
        """
        response = await self.client.post(
            f"https://scratch.mit.edu/site-api/galleries/all/{self.id}/report/",
            data=aiohttp.FormData({"selected_field":type})
        )
        data:ReportPayload|Literal[""] = response.json_or_text()
        if data == "":
            raise InvalidData(response)
        if not data.get("success"):
            raise InvalidData(response)
        return data.get("moderation_status")

    async def edit(
            self,
            title:str|None=None,
            description:str|None=None,
            trash:bool|None=None
        ) -> None:
        """
        スタジオを編集する。

        Args:
            title (str | None, optional): スタジオのタイトル
            description (str | None, optional): スタジオの説明欄
            trash (bool | None, optional): スタジオを削除するか
        """
        self.require_session()
        data = {}
        if description is not None: data["description"] = description + "\n"
        if title is not None: data["title"] = title
        if trash: data["visibility"] = "delbyusr"
        response = await self.client.put(f"https://scratch.mit.edu/site-api/galleries/all/{self.id}",json=data)
        self._update_from_data(response.json())

    async def set_thumbnail(self,thumbnail:File|bytes):
        """
        サムネイルを設定する。

        Args:
            thumbnail (file.File | bytes): サムネイルデータ
        """
        async with _read_file(thumbnail) as f:
            self.require_session()
            await self.client.post(
                f"https://scratch.mit.edu/site-api/galleries/all/{self.id}/",
                data=aiohttp.FormData({"file":f})
            )

    async def open_project(self):
        """
        プロジェクトを誰でも入れれるように変更する。
        """
        self.require_session()
        await self.client.put(f"https://scratch.mit.edu/site-api/galleries/{self.id}/mark/open/")

    async def close_project(self):
        """
        プロジェクトをキュレーター以上のみ入れれるように変更する。
        """
        self.require_session()
        await self.client.put(f"https://scratch.mit.edu/site-api/galleries/{self.id}/mark/closed/")

    async def toggle_comment(self):
        """
        コメント欄を開閉する。
        """
        self.require_session()
        await self.client.post(f"https://scratch.mit.edu/site-api/comments/gallery/{self.id}/toggle-comments/")

class StudioStatus:
    """
    スタジオでのステータスを表す。

    Attributes:s
        manager (bool): マネージャーか
        curator (bool): キュレーターか
        invited (bool): 招待されているか
        following (bool): フォローしているか
    """
    def __init__(self,data:StudioRolePayload,studio:Studio):
        self.studio:Studio = studio
        self.manager:bool = data.get("manager")
        self.curator:bool = data.get("curator")
        self.invited:bool = data.get("invited")
        self.following:bool = data.get("following")

def get_studio(studio_id:int,*,_client:HTTPClient|None=None) -> _AwaitableContextManager[Studio]:
    """
    スタジオを取得する。

    Args:
        studio_id (int): 取得したいスタジオのID

    Returns:
        common._AwaitableContextManager[Studio]: await か async with で取得できるスタジオ
    """
    return _AwaitableContextManager(Studio._create_from_api(studio_id,_client))

async def explore_studios(
        client:HTTPClient,
        query:explore_query="*",
        mode:search_mode="trending",
        language:str="en",
        limit:int|None=None,
        offset:int|None=None,
        *,
        session:Session|None=None
    ) -> AsyncGenerator[Studio]:
    """
    スタジオの傾向を取得する

    Args:
        client (HTTPClient): 使用するHTTPClient
        query (explore_query, optional): 取得するする種類。デフォルトは"*"(all)です。
        mode (Literal["trending","popular"], optional): 取得するモード。デフォルトは"trending"です。
        language (str, optional): 取得する言語。デフォルトは"en"です。
        limit (int|None, optional): 取得するスタジオの数。初期値は40です。
        offset (int|None, optional): 取得するスタジオの開始位置。初期値は0です。
        session (Session | None, optional): セッションを使用したい場合、使用したいセッション

    Yields:
        Studio:
    """
    client_or_session = session or client
    async for _s in api_iterative(
        client,"https://api.scratch.mit.edu/explore/studios",limit,offset,
        params={"language":language,"mode":mode,"q":query}
    ):
        yield Studio._create_from_data(_s["id"],_s,client_or_session)

async def search_studios(
        client:HTTPClient,
        query:str,
        mode:search_mode="trending",
        language:str="en",
        limit:int|None=None,
        offset:int|None=None,
        *,
        session:Session|None=None
    ) -> AsyncGenerator[Studio]:
    """
    スタジオを検索する

    Args:
        client (HTTPClient): 使用するHTTPClient
        query (str): 検索したい内容
        mode (Literal["trending","popular"], optional): 取得するモード。デフォルトは"trending"です。
        language (str, optional): 取得する言語。デフォルトは"en"です。
        limit (int|None, optional): 取得するスタジオの数。初期値は40です。
        offset (int|None, optional): 取得するスタジオの開始位置。初期値は0です。
        session (Session | None, optional): セッションを使用したい場合、使用したいセッション

    Yields:
        Studio:
    """
    client_or_session = session or client
    async for _s in api_iterative(
        client,"https://api.scratch.mit.edu/search/studios",limit,offset,
        params={"language":language,"mode":mode,"q":query}
    ):
        yield Studio._create_from_data(_s["id"],_s,client_or_session)