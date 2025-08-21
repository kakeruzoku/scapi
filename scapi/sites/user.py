import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Final
from ..utils import client, common, error
from . import base,session,project,user,studio,comment
from ..utils.types import (
    UserPayload,
    UserFeaturedPayload
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
        self.status:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.bio:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
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
    
    async def get_follower(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["user.User", None]:
        async for _u in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/followers/",
            limit=limit,offset=offset
        ):
            yield user.User._create_from_data(_u["username"],_u,self.client_or_session)

    async def get_following(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["user.User", None]:
        async for _u in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/following/",
            limit=limit,offset=offset
        ):
            yield user.User._create_from_data(_u["username"],_u,self.client_or_session)

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

    def get_comment(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator["comment.Comment", None]:
        return comment.get_comment_from_old(self,start_page,end_page)
    
    get_comment_from_old = get_comment


    async def post_comment(
        self,content:str,
        parent:"comment.Comment|int|None"=None,commentee:"user.User|int|None"=None,
        is_old:bool=True
    ) -> "comment.Comment":
        return await comment.Comment.post_comment(self,content,parent,commentee,is_old)
    
def get_user(username:str,*,_client:client.HTTPClient|None=None) -> common._AwaitableContextManager[User]:
    return common._AwaitableContextManager(User._create_from_api(username,_client))