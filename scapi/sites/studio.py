import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Final

import aiohttp
from ..utils import client, common, error, file
from . import base,project,user,session,comment
from ..utils.types import (
    StudioPayload,
    StudioRolePayload,
    OldStudioPayload
)

class Studio(base._BaseSiteAPI[int]):
    """
    スタジオを表す

    Attributes:
        id (int): スタジオのID
        title (common.MAYBE_UNKNOWN[str]): スタジオの名前
        host_id (common.MAYBE_UNKNOWN[int]): スタジオの所有者のユーザーID
        description (common.MAYBE_UNKNOWN[str]): スタジオの説明欄
        open_to_all (common.MAYBE_UNKNOWN[bool]): 誰でもプロジェクトを追加できるか
        comments_allowed (common.MAYBE_UNKNOWN[bool]): コメント欄が開いているか

        comment_count (common.MAYBE_UNKNOWN[int]): コメントの数(<=100)
        follower_count (common.MAYBE_UNKNOWN[int]): フォロワーの数
        manager_count (common.MAYBE_UNKNOWN[int]): マネージャーの数
        project_count (common.MAYBE_UNKNOWN[int]): プロジェクトの数(<=100)

        _host (common.MAYBE_UNKNOWN[User]): 所有者の情報。Session.get_mystuff_studios()からでのみ取得できます。
    """
    def __repr__(self) -> str:
        return f"<Studio id:{self.id} session:{self.session}>"

    def __init__(self,id:int,client_or_session:"client.HTTPClient|session.Session|None"=None):
        super().__init__(client_or_session)
        self.id:Final[int] = id
        self.title:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.host_id:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.description:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.open_to_all:common.MAYBE_UNKNOWN[bool] = common.UNKNOWN
        self.comments_allowed:common.MAYBE_UNKNOWN[bool] = common.UNKNOWN

        self._created_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self._modified_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN

        self.comment_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.follower_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.manager_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.project_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN

        self._host:common.MAYBE_UNKNOWN["user.User"] = common.UNKNOWN
    
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
        _author = data.get("owner")

        if _author:
            if self._host is common.UNKNOWN:
                self._host = user.User(_author.get("username"),self.client_or_session)
            self._host._update_from_old_data(_author)
        
        self._update_to_attributes(
            title=data.get("title"),

            _created_at=data.get("datetime_created"),
            _modified_at=data.get("datetime_modified"),

            comment_count=data.get("commenters_count"),
            curator_count=data.get("curators_count"),
            project_count=data.get("projecters_count"),
        )
    
    @property
    def created_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        """
        スタジオが作成された時間を返す

        Returns:
            datetime.datetime|UNKNOWN_TYPE: データがある場合、その時間。
        """
        return common.dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        """
        スタジオが最後に編集された時間を返す

        Returns:
            datetime.datetime|UNKNOWN_TYPE: データがある場合、その時間。
        """
        return common.dt_from_isoformat(self._modified_at)
    
    
    async def get_projects(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["project.Project", None]:
        """
        スタジオに入れられているプロジェクトを取得する。

        Args:
            limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
            offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。

        Yields:
            Project: 取得したプロジェクト
        """
        async for _p in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/projects",
            limit=limit,offset=offset
        ):
            yield project.Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_host(self) -> "user.User":
        """
        スタジオの所有者ユーザーを取得する。

        Returns:
            user.User: 取得したユーザー
        """
        return await anext(self.get_managers(limit=1))

    async def get_managers(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["user.User", None]:
        """
        スタジオのマネージャーを取得する。

        Args:
            limit (int|None, optional): 取得するユーザーの数。初期値は40です。
            offset (int|None, optional): 取得するユーザーの開始位置。初期値は0です。

        Yields:
            User: 取得したユーザー
        """
        async for _u in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/managers",
            limit=limit,offset=offset
        ):
            yield user.User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_curators(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["user.User", None]:
        """
        スタジオのキュレーターを取得する。

        Args:
            limit (int|None, optional): 取得するユーザーの数。初期値は40です。
            offset (int|None, optional): 取得するユーザーの開始位置。初期値は0です。

        Yields:
            User: 取得したユーザー
        """
        async for _u in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/curators",
            limit=limit,offset=offset
        ):
            yield user.User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_comments(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["comment.Comment", None]:
        """
        スタジオに投稿されたコメントを取得する。

        Args:
            limit (int|None, optional): 取得するコメントの数。初期値は40です。
            offset (int|None, optional): 取得するコメントの開始位置。初期値は0です。

        Yields:
            Comment: プロジェクトに投稿されたコメント
        """
        async for _c in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/comments",
            limit=limit,offset=offset
        ):
            yield comment.Comment._create_from_data(_c["id"],_c,place=self)

    async def get_comment_by_id(self,comment_id:int) -> "comment.Comment":
        """
        コメントIDからコメントを取得する。

        Args:
            comment_id (int): 取得したいコメントのID

        Raises:
            error.NotFound: コメントが見つからない
        
        Returns:
            Comment: 見つかったコメント
        """
        return await comment.Comment._create_from_api(comment_id,place=self)
    
    def get_comments_from_old(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator["comment.Comment", None]:
        """
        スタジオに投稿されたコメントを古いAPIから取得する。

        Args:
            start_page (int|None, optional): 取得するコメントの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するコメントの終了ページ位置。初期値はstart_pageの値です。

        Returns:
            Comment: 取得したコメント
        """
        return comment.get_comment_from_old(self,start_page,end_page)
    

    async def post_comment(
        self,content:str,
        parent:"comment.Comment|int|None"=None,commentee:"user.User|int|None"=None,
        is_old:bool=False
    ) -> "comment.Comment":
        """
        コメントを投稿します。

        Args:
            content (str): コメントの内容
            parent (Comment|int|None, optional): 返信する場合、返信元のコメントかID
            commentee (User|int|None, optional): メンションする場合、ユーザーかそのユーザーのID
            is_old (bool, optional): 古いAPIを使用して送信するか

        Returns:
            comment.Comment: 投稿されたコメント
        """
        return await comment.Comment.post_comment(self,content,parent,commentee,is_old)

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

    async def add_project(self,project_id:"project.Project|int"):
        """
        プロジェクトをスタジオに追加する。

        Args:
            project_id (project.Project|int): 追加するプロジェクトかそのID
        """
        self.require_session()
        project_id = project_id.id if isinstance(project_id,project.Project) else project_id
        await self.client.post(f"https://api.scratch.mit.edu/studios/{self.id}/project/{project_id}")

    async def remove_project(self,project_id:"project.Project|int"):
        """
        プロジェクトをスタジオから削除する。

        Args:
            project_id (project.Project|int): 削除するプロジェクトかそのID
        """
        self.require_session()
        project_id = project_id.id if isinstance(project_id,project.Project) else project_id
        await self.client.delete(f"https://api.scratch.mit.edu/studios/{self.id}/project/{project_id}")

    async def invite(self,username:"user.User|str"):
        """
        スタジオにユーザーを招待する

        Args:
            username (user.User|str): 招待したいユーザーかそのID
        """
        self.require_session()
        username = username.username if isinstance(username,user.User) else username
        response = await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/invite_curator/",
            params={"usernames":username}
        )
        data = response.json()
        if data.get("status") != "success":
            raise error.ClientError(response,data.get("message"))
        
    async def accept_invite(self):
        """
        招待を受け取る
        """
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/add/",
            params={"usernames":self._session.username}
        )

    async def promote(self,username:"user.User|str"):
        """
        ユーザーをマネージャーに昇格する

        Args:
            username (user.User|str): 昇格したいユーザーかそのID
        """
        self.require_session()
        username = username.username if isinstance(username,user.User) else username
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/promote/",
            params={"usernames":username}
        )
    
    async def remove_curator(self,username:"user.User|str"):
        """
        スタジオからユーザーを削除する。

        Args:
            username (user.User|str): 削除したいユーザーかそのID
        """
        self.require_session()
        username = username.username if isinstance(username,user.User) else username
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/remove/",
            params={"usernames":username}
        )

    async def leave(self):
        """
        スタジオからぬける
        """
        await self.remove_curator(self._session.username)

    async def transfer_ownership(self,username:"str|user.User",password:str):
        """
        スタジオの所有権を移行する

        Args:
            username (str|user.User): 新たな所有者かそのユーザー名
            password (str): このアカウントのパスワード
        """
        self.require_session()
        username = username.username if isinstance(username,user.User) else username
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

    async def set_thumbnail(self,thumbnail:file.File|bytes):
        """
        サムネイルを設定する。

        Args:
            thumbnail (file.File | bytes): サムネイルデータ
        """
        async with file._read_file(thumbnail) as f:
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

def get_studio(studio_id:int,*,_client:client.HTTPClient|None=None) -> common._AwaitableContextManager[Studio]:
    """
    スタジオを取得する。

    Args:
        studio_id (int): 取得したいスタジオのID

    Returns:
        common._AwaitableContextManager[Studio]: await か async with で取得できるスタジオ
    """
    return common._AwaitableContextManager(Studio._create_from_api(studio_id,_client))