from typing import TYPE_CHECKING, AsyncGenerator, Final
from ..utils import client, common, error
from . import base,session,project,user,studio
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
        self.id:int|None = None

        self._joined_at:str|None = None

        self.profile_id:int|None = None
        self.status:str|None = None
        self.bio:str|None = None
        self.country:str|None = None
        self.scratchteam:bool|None = None

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
    def joined_at(self):
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
    
def get_user(username:str,*,_client:client.HTTPClient|None=None) -> common._AwaitableContextManager[User]:
    return common._AwaitableContextManager(User._create_from_api(username,_client))