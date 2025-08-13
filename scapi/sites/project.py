import json
from typing import TYPE_CHECKING, AsyncGenerator
from ..others import client, common, error
from . import base
from ..others.types import (
    ProjectPayload
)
from . import user,studio,session

class Project(base._BaseSiteAPI[int]):
    def __repr__(self) -> str:
        return f"<Project id:{self.id} author:{self.author} session:{self.session}>"

    def __init__(self,id:int,client_or_session:"client.HTTPClient|session.Session|None"=None):
        super().__init__(client_or_session)
        self.id:int = id
        self.title:str|None = None

        self.author:"user.User|None" = None
        self.instructions:str|None = None
        self.description:str|None = None
        self.public:bool|None = None
        self.comments_allowed:bool|None = None
        
        self._created_at:str|None = None
        self._modified_at:str|None = None
        self._shared_at:str|None = None

        self.view_count:int|None = None
        self.love_count:int|None = None
        self.favorite_count:int|None = None
        self.remix_count:int|None = None

        self.remix_parent_id:int|None = None
        self.remix_root_id:int|None = None
    
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
            if self.author is None:
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
    def created_at(self):
        return common.dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self):
        return common.dt_from_isoformat(self._modified_at)
    
    @property
    def shared_at(self):
        return common.dt_from_isoformat(self._shared_at)
    
    async def get_remix(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Project", None]:
        async for _p in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/projects/{self.id}/remixes",
            limit=limit,offset=offset
        ):
            p = Project(_p["id"],self.client_or_session)
            p._update_from_data(_p)
            yield p

    async def get_studio(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["studio.Studio", None]:
        async for _p in common.api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self._author_username}/projects/{self.id}/studios",
            limit=limit,offset=offset
        ):
            p = studio.Studio(_p["id"],self.client_or_session)
            p._update_from_data(_p)
            yield p

    async def get_parent_project(self) -> "Project|None":
        if self.remix_parent_id:
            return await self._create_from_api(self.remix_parent_id,self.client_or_session)
        
    async def get_root_project(self) -> "Project|None":
        if self.remix_root_id:
            return await self._create_from_api(self.remix_root_id,self.client_or_session)


    async def create_remix(self,title:str|None=None) -> "Project":
        #TODO download project
        return await self._session.create_project(title,remix_id=self.id)
    
    async def edit_project(self,project_json:dict|str|bytes):
        self._check_owner()

        if isinstance(project_json,dict):
            _data = json.dumps(project_json)
            content_type = "application/json"
        elif isinstance(project_json,str):
            _data = project_json
            content_type = "application/json"
        elif isinstance(project_json,bytes):
            _data = project_json
            content_type = "application/zip"
        else:
            raise TypeError()
        headers = self.client.scratch_headers|{"Content-Type": content_type}

        await self.client.put(
            f"https://projects.scratch.mit.edu/{self.id}",
            data=_data,headers=headers
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

def get_project(project_id:int,*,_client:client.HTTPClient|None=None) -> common._AwaitableContextManager[Project]:
    return common._AwaitableContextManager(Project._create_from_api(project_id,_client))