from typing import TYPE_CHECKING
from ..others import client, common
from . import base
from ..others.types import (
    StudioPayload
)

if TYPE_CHECKING:
    from . import session

class Studio(base._BaseSiteAPI[int]):
    def __repr__(self) -> str:
        return f"<Studio id:{self.id} session:{self.session}>"

    def __init__(self,id:int,client_or_session:"client.HTTPClient|session.Session|None"=None):
        super().__init__(client_or_session)
        self.id:int = id
        self.title:str|None = None
        self.host_id:int|None = None
        self.description:str|None = None
        self.open_to_all:bool|None = None
        self.comments_allowed:bool|None = None

        self._created_at:str|None = None
        self._modified_at:str|None = None

        self.comment_count:int|None = None
        self.follower_count:int|None = None
        self.manager_count:int|None = None
        self.project_count:int|None = None
    
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
    def created_at(self):
        return common.dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self):
        return common.dt_from_isoformat(self._modified_at)
    

def get_studio(studio_id:int,*,_client:client.HTTPClient|None=None) -> common._AwaitableContextManager[Studio]:
    return common._AwaitableContextManager(Studio._create_from_api(studio_id,_client))