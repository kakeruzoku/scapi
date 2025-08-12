from typing import TYPE_CHECKING, AsyncGenerator
from ..others import client, common, error
from . import base
from ..others.types import (
    ProjectPayload
)

if TYPE_CHECKING:
    from . import session

class Project(base._BaseSiteAPI[int]):

    def __init__(self,id:int,client_or_session:"client.HTTPClient|session.Session|None"=None):
        super().__init__(client_or_session)
        self.id:int = id
        self.title:str|None = None

        self.author = None
        self.description:str|None = None
        self.instructions:str|None = None
        self.public:bool|None = None
        self.comments_allowed:bool|None = None
        
        self._created_at:str|None = None
        self._modified_at:str|None = None
        self._shared_at:str|None = None

        self.views:int|None = None
        self.loves:int|None = None
        self.favorites:int|None = None
        self.remixes:int|None = None

        self.remix_parent_id:int|None = None
        self.remix_root_id:int|None = None
    
    async def update(self):
        response = await self.client.get(f"https://api.scratch.mit.edu/projects/{self.id}")
        self._update_from_data(response.json())

    def _update_from_data(self, data:ProjectPayload):
        self._update_to_attributes({
            "title":data.get("title"),
            "description":data.get("description"),
            "instructions":data.get("instructions"),
            "public":data.get("public"),
            "comments_allowed":data.get("comments_allowed"),
        })

        _history = data.get("history")
        if _history:
            self._update_to_attributes({
                "_created_at":_history.get("created"),
                "_modified_at":_history.get("modified"),
                "_shared_at":_history.get("shared")
            })

        _stats = data.get("stats")
        if _stats:
            self._update_to_attributes({
                "views":_stats.get("views"),
                "loves":_stats.get("loves"),
                "favorites":_stats.get("favorites"),
                "remixes":_stats.get("remixes")
            })

        _remix = data.get("remix")
        if _remix:
            self._update_to_attributes({
                "remix_parent_id":_remix.get("parent"),
                "remix_root_id":_remix.get("root")
            })
    
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

def get_project(project_id:int,*,_client:client.HTTPClient|None=None) -> common._AwaitableContextManager[Project]:
    return common._AwaitableContextManager(Project._create_from_api(project_id,_client))