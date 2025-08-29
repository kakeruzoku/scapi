import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Final

import aiohttp
from ..utils import client, common, error, file
from . import base,project,user,session,comment
from ..utils.types import (
    StudioPayload,
    StudioRolePayload
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
    
    @property
    def created_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        return common.dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        return common.dt_from_isoformat(self._modified_at)
    
    
    async def get_projects(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["project.Project", None]:
        async for _p in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/projects",
            limit=limit,offset=offset
        ):
            yield project.Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_host(self) -> "user.User":
        return await anext(self.get_managers(limit=1))

    async def get_managers(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["user.User", None]:
        async for _u in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/managers",
            limit=limit,offset=offset
        ):
            yield user.User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_curators(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["user.User", None]:
        async for _u in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/curators",
            limit=limit,offset=offset
        ):
            yield user.User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_comments(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["comment.Comment", None]:
        async for _c in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/studios/{self.id}/comments",
            limit=limit,offset=offset
        ):
            yield comment.Comment._create_from_data(_c["id"],_c,place=self)

    async def get_comment_by_id(self,comment_id:int) -> "comment.Comment":
        return await comment.Comment._create_from_api(comment_id,place=self)
    
    def get_comments_from_old(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator["comment.Comment", None]:
        return comment.get_comment_from_old(self,start_page,end_page)
    

    async def post_comment(
        self,content:str,
        parent:"comment.Comment|int|None"=None,commentee:"user.User|int|None"=None,
        is_old:bool=False
    ) -> "comment.Comment":
        self.require_session()
        return await comment.Comment.post_comment(self,content,parent,commentee,is_old)

    async def follow(self):
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/bookmarkers/{self.id}/add/",
            params={"usernames":self._session.username}
        )

    async def unfollow(self):
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/bookmarkers/{self.id}/remove/",
            params={"usernames":self._session.username}
        )

    async def add_project(self,project_id:"project.Project|int"):
        self.require_session()
        project_id = project_id.id if isinstance(project_id,project.Project) else project_id
        await self.client.post(f"https://api.scratch.mit.edu/studios/{self.id}/project/{project_id}")

    async def remove_project(self,project_id:"project.Project|int"):
        self.require_session()
        project_id = project_id.id if isinstance(project_id,project.Project) else project_id
        await self.client.delete(f"https://api.scratch.mit.edu/studios/{self.id}/project/{project_id}")

    async def invite(self,username:"user.User|str"):
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
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/add/",
            params={"usernames":self._session.username}
        )

    async def promote(self,username:"user.User|str"):
        self.require_session()
        username = username.username if isinstance(username,user.User) else username
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/promote/",
            params={"usernames":username}
        )
    
    async def remove_curator(self,username:"user.User|str"):
        self.require_session()
        username = username.username if isinstance(username,user.User) else username
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/remove/",
            params={"usernames":username}
        )

    async def leave(self):
        await self.remove_curator(self._session.username)

    async def transfer_ownership(self,username:"str|user.User",password:str):
        self.require_session()
        username = username.username if isinstance(username,user.User) else username
        await self.client.put(
            f"https://api.scratch.mit.edu/studios/{self.id}/transfer/{username}",
            json={"password":password}
        )

    async def get_my_role(self) -> "StudioStatus":
        response = await self.client.get(f"https://api.scratch.mit.edu/studios/{self.id}/users/{self._session.username}")
        return StudioStatus(response.json(),self)
    

    async def edit(
            self,
            title:str|None=None,
            description:str|None=None,
            trash:bool|None=None
        ) -> None:
        self.require_session()
        data = {}
        if description is not None: data["description"] = description + "\n"
        if title is not None: data["title"] = title
        if trash: data["visibility"] = "delbyusr"
        response = await self.client.put(f"https://scratch.mit.edu/site-api/galleries/all/{self.id}",json=data)
        self._update_from_data(response.json())

    async def set_thumbnail(self,thumbnail:file.File|bytes):
        async with file._read_file(thumbnail) as f:
            self.require_session()
            await self.client.post(
                f"https://scratch.mit.edu/site-api/galleries/all/{self.id}/",
                data=aiohttp.FormData({"file":f})
            )

    async def open_project(self):
        self.require_session()
        await self.client.put(f"https://scratch.mit.edu/site-api/galleries/{self.id}/mark/open/")

    async def close_project(self):
        self.require_session()
        await self.client.put(f"https://scratch.mit.edu/site-api/galleries/{self.id}/mark/closed/")

    async def toggle_comment(self):
        self.require_session()
        await self.client.post(f"https://scratch.mit.edu/site-api/comments/gallery/{self.id}/toggle-comments/")

class StudioStatus:
    def __init__(self,data:StudioRolePayload,studio:Studio):
        self.studio = studio
        self.manager = data.get("manager")
        self.curator = data.get("curator")
        self.invited = data.get("invited")
        self.following = data.get("following")

def get_studio(studio_id:int,*,_client:client.HTTPClient|None=None) -> common._AwaitableContextManager[Studio]:
    return common._AwaitableContextManager(Studio._create_from_api(studio_id,_client))