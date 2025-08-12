from typing import TYPE_CHECKING
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

    @property
    def update_url(self):
        return f"https://api.scratch.mit.edu/projects/{self.id}"
    
    def update_from_data(self, data:ProjectPayload) -> bool:
        
        self._update({
            "title":data.get("title"),
            "description":data.get("description"),
            "instructions":data.get("instructions"),
            "public":data.get("public"),
            "comments_allowed":data.get("comments_allowed"),
        })

        _history = data.get("history")
        if _history:
            self._update({
                "_created_at":_history.get("created"),
                "_modified_at":_history.get("modified"),
                "_shared_at":_history.get("shared")
            })

        _stats = data.get("stats")
        if _stats:
            self._update({
                "views":_stats.get("views"),
                "loves":_stats.get("loves"),
                "favorites":_stats.get("favorites"),
                "remixes":_stats.get("remixes")
            })

        _remix = data.get("remix")
        if _remix:
            self._update({
                "remix_parent_id":_remix.get("parent"),
                "remix_root_id":_remix.get("root")
            })


        return True