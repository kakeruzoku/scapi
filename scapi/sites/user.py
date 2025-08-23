import datetime
from enum import Enum
import random
from typing import TYPE_CHECKING, AsyncGenerator, Final

import aiohttp
from ..utils import client, common, error, file
from . import base,session,project,studio,comment
from ..utils.types import (
    UserPayload,
    UserMessageCountPayload
)

class User(base._BaseSiteAPI[str]):
    def __repr__(self) -> str:
        return f"<User username:{self.username} id:{self.id} session:{self.session}>"

    def __init__(self,username:str,client_or_session:"client.HTTPClient|session.Session|None"=None):
        super().__init__(client_or_session)
        self.username:Final[str] = username
        self.id:common.MAYBE_UNKNOWN[int] = common.UNKNOWN

        self._joined_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN

        self.profile_id:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.bio:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.status:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.country:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.scratchteam:common.MAYBE_UNKNOWN[bool] = common.UNKNOWN

    async def update(self):
        response = await self.client.get(f"https://api.scratch.mit.edu/users/{self.username}")
        self._update_from_data(response.json())

    def _update_from_data(self, data:UserPayload):
        self._update_to_attributes(
            id=data.get("id"),
            scratchteam=data.get("scratchteam")
        )
        _history = data.get("history")
        if _history:
            self._update_to_attributes(_joined_at=_history.get("joined"))
        
        _profile = data.get("profile")
        if _profile:
            self._update_to_attributes(
                profile_id=_profile.get("id"),
                status=_profile.get("status"),
                bio=_profile.get("bio")
            )
    
    @property
    def joined_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        return common.dt_from_isoformat(self._joined_at)
    

    async def get_featured(self) -> "project.ProjectFeatured|None":
        response = await self.client.get(f"https://scratch.mit.edu/site-api/users/all/{self.username}/")
        return project.ProjectFeatured(response.json(),self)
    
    async def get_follower(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["User", None]:
        async for _u in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/followers/",
            limit=limit,offset=offset
        ):
            yield User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_following(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["User", None]:
        async for _u in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/following/",
            limit=limit,offset=offset
        ):
            yield User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_project(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["project.Project", None]:
        async for _p in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/projects/",
            limit=limit,offset=offset
        ):
            yield project.Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_favorite(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["project.Project", None]:
        async for _p in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/favorites/",
            limit=limit,offset=offset
        ):
            yield project.Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_studio(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["studio.Studio", None]:
        async for _s in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/studios/curate",
            limit=limit,offset=offset
        ):
            yield studio.Studio._create_from_data(_s["id"],_s,self.client_or_session)

    async def get_message_count(self) -> int:
        response = await self.client.get(
            f"https://api.scratch.mit.edu/users/{self.username}/messages/count/",
            params={"cachebust":str(random.randint(0,10000))}
        )
        data:UserMessageCountPayload = response.json()
        return data.get("count")

    def get_comment(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator["comment.Comment", None]:
        return comment.get_comment_from_old(self,start_page,end_page)
    
    get_comment_from_old = get_comment


    async def post_comment(
        self,content:str,
        parent:"comment.Comment|int|None"=None,commentee:"User|int|None"=None,
        is_old:bool=True
    ) -> "comment.Comment":
        self.require_session()
        return await comment.Comment.post_comment(self,content,parent,commentee,is_old)
    
    async def follow(self):
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/followers/{self.username}/add/",
            params={"usernames":self._session.username}
        )

    async def unfollow(self):
        await self.client.put(
            f"https://scratch.mit.edu/site-api/users/followers/{self.username}/remove/",
            params={"usernames":self._session.username}
        )


    async def edit(
            self,*,
            bio:str|None=None,
            status:str|None=None,
            featured_project_id:int|None=None,
            featured_project_label:"ProjectFeaturedLabel|None"=None
        ) -> "None | project.ProjectFeatured":
        _data = {}
        if bio is not None: _data["bio"] = bio
        if status is not None: _data["status"] = status
        if featured_project_id is not None: _data["featured_project"] = featured_project_id
        if featured_project_label is not None: _data["featured_project_label"] = featured_project_label.value

        response = await self.client.put(f"https://scratch.mit.edu/site-api/users/all/{self.username}/",json=_data)
        data = response.json()
        if data.get("errors"):
            raise error.ClientError(response)
        return project.ProjectFeatured(data,self)

    async def toggle_comment(self):
        await self.client.post(f"https://scratch.mit.edu/site-api/comments/user/{self.username}/toggle-comments/")

    async def set_icon(self,icon:file.File|bytes):
        async with file._read_file(icon) as f:
            self.require_session()
            await self.client.post(
                f"https://scratch.mit.edu/site-api/users/all/{self.id}/",
                data=aiohttp.FormData({"file":f})
            )


class ProjectFeaturedLabel(Enum):
    ProjectFeatured=""
    Tutorial="0"
    WorkInProgress="1"
    RemixThis="2"
    MyFavoriteThings="3"
    WhyIScratch="4"

    @classmethod
    async def get_from_id(cls,id:int|None) -> "ProjectFeaturedLabel":
        if id is None:
            return cls.ProjectFeatured
        _id = str(id)
        for item in cls:
            if item.value == _id:
                return item
        raise ValueError()

def get_user(username:str,*,_client:client.HTTPClient|None=None) -> common._AwaitableContextManager[User]:
    return common._AwaitableContextManager(User._create_from_api(username,_client))