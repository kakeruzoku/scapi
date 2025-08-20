import datetime
import json
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final, Literal
from ..utils import client, common, error, file
from . import base
from ..utils.types import (
    ProjectPayload,
    ProjectLovePayload,
    ProjectFavoritePayload,
    ProjectVisibilityPayload,
    UserFeaturedPayload
)
from . import user,studio,session

class Project(base._BaseSiteAPI[int]):
    def __repr__(self) -> str:
        return f"<Project id:{self.id} author:{self.author} session:{self.session}>"

    def __init__(self,id:int,client_or_session:"client.HTTPClient|session.Session|None"=None):
        super().__init__(client_or_session)
        self.id:Final[int] = id
        self.title:common.MAYBE_UNKNOWN[str] = common.UNKNOWN

        self.author:"common.MAYBE_UNKNOWN[user.User]" = common.UNKNOWN
        self.instructions:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.description:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.public:common.MAYBE_UNKNOWN[bool] = common.UNKNOWN
        self.comments_allowed:common.MAYBE_UNKNOWN[bool] = common.UNKNOWN
        
        self._created_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self._modified_at:common.MAYBE_UNKNOWN[str|None] = common.UNKNOWN
        self._shared_at:common.MAYBE_UNKNOWN[str|None] = common.UNKNOWN

        self.view_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.love_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.favorite_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.remix_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN

        self.remix_parent_id:common.MAYBE_UNKNOWN[int|None] = common.UNKNOWN
        self.remix_root_id:common.MAYBE_UNKNOWN[int|None] = common.UNKNOWN
    
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
        )
        
        _author = data.get("author")
        if _author:
            if self.author is common.UNKNOWN:
                self.author = user.User(_author.get("username"),self.client_or_session)
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

    @property
    def _author_username(self) -> str:
        if not (self.author and self.author.username):
            raise error.NoDataError(self)
        return self.author.username
    
    @common._bypass_checking
    def _check_owner(self):
        if self._author_username.lower() != self._session.username.lower():
            raise error.NoPermission(self)
    
    @property
    def created_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        return common.dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self) -> datetime.datetime|common.UNKNOWN_TYPE|None:
        return common.dt_from_isoformat(self._modified_at)
    
    @property
    def shared_at(self) -> datetime.datetime|common.UNKNOWN_TYPE|None:
        return common.dt_from_isoformat(self._shared_at)
    
    async def get_remix(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Project", None]:
        async for _p in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/projects/{self.id}/remixes",
            limit=limit,offset=offset
        ):
            yield Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_studio(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["studio.Studio", None]:
        async for _s in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self._author_username}/projects/{self.id}/studios",
            limit=limit,offset=offset
        ):
            yield studio.Studio._create_from_data(_s["id"],_s,self.client_or_session)

    async def get_parent_project(self) -> "Project|None":
        if self.remix_parent_id:
            return await self._create_from_api(self.remix_parent_id,self.client_or_session)
        
    async def get_root_project(self) -> "Project|None":
        if self.remix_root_id:
            return await self._create_from_api(self.remix_root_id,self.client_or_session)

    async def edit_project(
            self,project_data:file.File|dict|str|bytes,is_json:bool|None=None
        ):
        self._check_owner()

        if isinstance(project_data,dict):
            project_data = json.dumps(project_data)
        if isinstance(project_data,(bytes, bytearray, memoryview)):
            is_json = False
        elif isinstance(project_data,str):
            is_json = True

        _data = file._file(project_data)

        content_type = "application/json" if is_json else "application/zip"
        headers = self.client.scratch_headers | {"Content-Type": content_type}
        await self.client.put(
            f"https://projects.scratch.mit.edu/{self.id}",
            data=_data.fp,headers=headers
        )

    async def edit(
            self,*,
            comment_allowed:bool|None=None,
            title:str|None=None,
            instructions:str|None=None,
            description:str|None=None,
        ):
        self._check_owner()

        data = {}
        if comment_allowed is not None: data["comment_allowed"] = comment_allowed
        if title is not None: data["title"] = title
        if instructions is not None: data["instructions"] = instructions
        if description is not None: data["description"] = description

        r = await self.client.put(
            f"https://api.scratch.mit.edu/projects/{self.id}",
            json=data
        )
        self._update_from_data(r.json())

    async def share(self):
        self._check_owner()
        await self.client.put(f"https://api.scratch.mit.edu/proxy/projects/{self.id}/share")
        self.public = True

    async def unshare(self):
        self._check_owner()
        await self.client.put(f"https://api.scratch.mit.edu/proxy/projects/{self.id}/unshare")
        self.public = False

    async def get_visibility(self) -> "ProjectVisibility":
        self._check_owner()
        response = await self.client.get(f"https://api.scratch.mit.edu/users/{self._session.username}/projects/{self.id}/visibility")
        return ProjectVisibility(response.json(),self)


    async def create_remix(self,title:str|None=None) -> "Project":
        #TODO download project
        return await self._session.create_project(title,remix_id=self.id)
    
    async def is_loved(self):
        response = await self.client.get(f"https://api.scratch.mit.edu/projects/{self.id}/loves/user/{self._session.username}")
        data:ProjectLovePayload = response.json()
        return data.get("userLove")

    async def add_love(self) -> bool:
        response = await self.client.post(f"https://api.scratch.mit.edu/projects/{self.id}/loves/user/{self._session.username}")
        data:ProjectLovePayload = response.json()
        return data.get("statusChanged")
    
    async def remove_love(self) -> bool:
        response = await self.client.delete(f"https://api.scratch.mit.edu/projects/{self.id}/loves/user/{self._session.username}")
        data:ProjectLovePayload = response.json()
        return data.get("statusChanged")
    
    async def is_favorited(self):
        response = await self.client.get(f"https://api.scratch.mit.edu/projects/{self.id}/favorites/user/{self._session.username}")
        data:ProjectFavoritePayload = response.json()
        return data.get("userFavorite")

    async def add_favorite(self) -> bool:
        response = await self.client.post(f"https://api.scratch.mit.edu/projects/{self.id}/favorites/user/{self._session.username}")
        data:ProjectFavoritePayload = response.json()
        return data.get("statusChanged")
    
    async def remove_favorite(self) -> bool:
        response = await self.client.delete(f"https://api.scratch.mit.edu/projects/{self.id}/favorites/user/{self._session.username}")
        data:ProjectFavoritePayload = response.json()
        return data.get("statusChanged")
    
    async def add_view(self) -> bool:
        try:
            await self.client.post(f"https://api.scratch.mit.edu/users/{self._author_username}/projects/{self.id}/views/")
        except error.TooManyRequests:
            return False
        else:
            return True
        

class ProjectVisibility:
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
    def __repr__(self):
        return repr(self.project)

    def __new__(cls,data:UserFeaturedPayload,_user:"user.User"):
        _project = data.get("featured_project_data")
        if _project is None:
            return
        else:
            return super().__new__(cls)

    def __init__(self,data:UserFeaturedPayload,_user:"user.User"):
        _project = data.get("featured_project_data")
        _user_payload = data.get("user")
        assert _project

        self.project = Project(int(_project.get("id")),_user.client_or_session)
        self.project._modified_at = _project.get("datetime_modified") + "Z"
        self.project.title = _project.get("title")

        self.author = self.project.author = _user
        self.author.id = data.get("id")
        self.author.profile_id = _user_payload.get("pk")

        self.label = data.get("featured_project_label_name")


def get_project(project_id:int,*,_client:client.HTTPClient|None=None) -> common._AwaitableContextManager[Project]:
    return common._AwaitableContextManager(Project._create_from_api(project_id,_client))