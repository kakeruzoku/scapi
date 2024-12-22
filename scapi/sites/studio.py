import datetime
import random
from typing import AsyncGenerator, TYPE_CHECKING


from ..others import common as common
from ..others import error as exception
from . import base
from .comment import Comment

if TYPE_CHECKING:
    from .session import Session
    from .user import User

class Studio(base._BaseSiteAPI):
    raise_class = exception.StudioNotFound
    id_name = "id"

    def __init__(
        self,
        ClientSession:common.Requests,
        id:int,
        scratch_session:"Session|None"=None,
        **entries
    ):
        super().__init__("get",f"https://api.scratch.mit.edu/studios/{id}",ClientSession,scratch_session)

        self.id = id
        self.title:str = None
        self.description:str = None
        self.author_id:int = None

        self.open_to_all:bool = None
        self.comments_allowed:bool = None

        self._created:str = None
        self._modified:str = None
        self.created:datetime.datetime = None
        self.modified:datetime.datetime = None

        self.follower_count:int = None
        self.manager_count:int = None
        self.project_count:int = None

    def _update_from_dict(self, data:dict):
        self.title = data.get("title",self.title)
        self.description = data.get("description",self.description)
        self.author_id = data.get("host",self.author_id)

        self.open_to_all = data.get("open_to_all",self.open_to_all)
        self.comments_allowed = data.get("comments_allowed",self.comments_allowed)

        _history:dict = data.get("history",{})
        self._created = _history.get("created",self._created)
        self.created = common.to_dt(self._created)
        self._modified = _history.get("modified",self._modified)
        self.modified = common.to_dt(self._modified)

        _stats:dict = data.get("stats",{})
        self.follower_count = _stats.get("followers",self.follower_count)
        self.manager_count = _stats.get("managers",self.manager_count)
        self.project_count = _stats.get("projects",self.project_count)

    @property
    def image_url(self) -> str:
        return f"https://cdn2.scratch.mit.edu/get_image/gallery/{self.id}_170x100.png"
    
    @property
    def url(self) -> str:
        return f"https://scratch.mit.edu/studios/{self.id}/"

    async def get_comment_by_id(self,id:int) -> Comment:
        return await base.get_object(
            self.ClientSession,{"place":self,"id":id,"data":None},Comment,self.Session
        )

    def get_comments(self, *, limit=40, offset=0) -> AsyncGenerator[Comment, None]:
        return base.get_comment_iterator(
            self,f"https://api.scratch.mit.edu/studios/{self.id}/comments",
            limit=limit,offset=offset,add_params={"cachebust":random.randint(0,9999)}
        )
    
    async def post_comment(self, content, *, parent_id="", commentee_id="") -> Comment:
        self.has_session()
        data = {
            "commentee_id": commentee_id,
            "content": str(content),
            "parent_id": parent_id,
        }
        header = self.ClientSession._header|{
            "referer":self.url
        }
        resp = (await self.ClientSession.post(
            f"https://api.scratch.mit.edu/proxy/comments/studio/{self.id}/",
            header=header,json=data
        )).json()
        return Comment(
            self.ClientSession,{"place":self,"data":resp,"id":resp["id"]},self.Session
        )
    
async def get_studio(studio_id:int,*,ClientSession=None) -> Studio:
    ClientSession = common.create_ClientSession(ClientSession)
    return await base.get_object(ClientSession,studio_id,Studio)

def create_Partial_Studio(studio_id:int,*,ClientSession=None) -> Studio:
    ClientSession = common.create_ClientSession(ClientSession)
    return Studio(ClientSession,studio_id)

def explore_studios(*, query:str="*", mode:str="trending", language:str="en", limit:int=40, offset:int=0,ClientSession:common.Requests=None) -> AsyncGenerator["Studio",None]:
    ClientSession = common.create_ClientSession(ClientSession)
    return base.get_object_iterator(
        ClientSession, f"https://api.scratch.mit.edu/explore/studios",
        None,Studio,limit=limit,offset=offset,
        add_params={"language":language,"mode":mode,"q":query}
    )

def search_studios(query:str, *, mode:str="trending", language:str="en", limit:int=40, offset:int=0,ClientSession:common.Requests=None) -> AsyncGenerator["Studio",None]:
    ClientSession = common.create_ClientSession(ClientSession)
    return base.get_object_iterator(
        ClientSession, f"https://api.scratch.mit.edu/search/studios",
        None,Studio,limit=limit,offset=offset,
        add_params={"language":language,"mode":mode,"q":query}
    )