import datetime
import random
from typing import AsyncGenerator, TYPE_CHECKING


from ..others import common
from ..others import error as exception
from . import base
from .comment import Comment

if TYPE_CHECKING:
    from .session import Session
    from .user import User
    from .studio import Studio

class Project(base._BaseSiteAPI):
    raise_class = exception.ObjectNotFound
    id_name = "id"

    def __init__(
        self,
        ClientSession:common.Requests,
        id:int,
        scratch_session:"Session|None"=None,
        **entries
    ) -> None:
        super().__init__("get",f"https://api.scratch.mit.edu/projects/{id}",ClientSession,scratch_session)

        self.id:int = id
        self.project_token:str = None
        
        self.author:"User" = None
        self.title:str = None
        self.instructions:str = None
        self.notes:str = None

        self.loves:int = None
        self.favorites:int = None
        self.remix_count:int = None
        self.views:int = None

        self._created:str = None
        self._shared:str = None
        self._modified:str = None
        self.created:datetime.datetime = None
        self.shared:datetime.datetime = None
        self.modified:datetime.datetime = None

        self.comments_allowed:bool = None
        self.remix_parent:int|None = None
        self.remix_root:int|None = None

    def _update_from_dict(self, data:dict) -> None:
        from .user import User
        _author:dict = data.get("author",{})
        self.author = User(self.ClientSession,_author.get("username",None),self.Session)
        self.author._update_from_dict(_author)
        
        self.comments_allowed = data.get("comments_allowed",self.comments_allowed)
        self.instructions = data.get("instructions",self.instructions)
        self.notes = data.get("description",self.notes)
        self.title:str = data.get("title")
        self.project_token:str = data.get("project_token")

        _history:dict = data.get("history",{})
        self._created = _history.get("created",self._created)
        self.created = common.to_dt(self._created)
        self._modified = _history.get("modified",self._modified)
        self.modified = common.to_dt(self._modified)
        self._shared = _history.get("shared",self._shared)
        self.shared = common.to_dt(self._shared)

        _remix:dict = data.get("remix",{})
        self.remix_parent = _remix.get("parent",self.remix_parent)
        self.remix_root = _remix.get("root",self.remix_root)

        _stats:dict = data.get("stats",{})
        self.favorites = _stats.get("favorites",self.favorites)
        self.loves = _stats.get("loves",self.loves)
        self.remix_count = _stats.get("remixes",self.remix_count)
        self.views = _stats.get("views",self.views)

    @property
    def _is_me(self) -> bool:
        common.no_data_checker(self.author)
        common.no_data_checker(self.author.username)
        if isinstance(self.Session,Session):
            if self.Session.username == self.author.username:
                return True
        return False
    
    @property
    def thumbnail_url(self) -> str:
        return f"https://cdn2.scratch.mit.edu/get_image/project/{self.id}_480x360.png"
    
    @property
    def url(self) -> str:
        return f"https://scratch.mit.edu/projects/{self.id}/"
    
    def _is_me_raise(self) -> None:
        if not self._is_me:
            raise exception.NoPermission
        
    def __eq__(self, value:object) -> bool:
        return isinstance(value,Project) and value.id == self.id

    def remixes(self, *, limit=40, offset=0) -> AsyncGenerator["Project",None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/projects/{self.id}/remixes",
            None,Project,self.Session,
            limit=limit,offset=offset
        )
    
    async def create_remix(self,title:str|None=None) -> "Project":
        self.has_session()
        try:
            project_json = self.download()
        except:
            project_json = common.empty_project_json
        if title is None:
            if self.title is None:
                title = f"{self.id} remix"
            else:
                title = f"{self.title} remix"

        return await self.Session.create_project(title,project_json,self.id)

    async def download(self) -> dict:
        try:
            self.update()
            return (await self.ClientSession.get(
                f"https://projects.scratch.mit.edu/{self.id}?token={self.project_token}"
            )).json()
        except Exception as e:
            raise exception.ProjectNotFound(Project,e)
        
    def studios(self, *, limit=40, offset=0) -> AsyncGenerator["Studio",None]:
        common.no_data_checker(self.author)
        common.no_data_checker(self.author.username)
        from .studio import Studio
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/users/{self.author.username}/projects/{self.id}/studios",
            None,Studio,self.Session,
            limit=limit,offset=offset
        )
    
    async def get_comment_by_id(self,id:int) -> Comment:
        common.no_data_checker(self.author)
        common.no_data_checker(self.author.username)
        return await base.get_object(
            self.ClientSession,{"place":self,"id":id,"data":None},Comment,self.Session
        )

    def get_comments(self, *, limit=40, offset=0) -> AsyncGenerator[Comment, None]:
        common.no_data_checker(self.author)
        common.no_data_checker(self.author.username)
        return base.get_comment_iterator(
            self,f"https://api.scratch.mit.edu/users/{self.author.username}/projects/{self.id}/comments",
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
            f"https://api.scratch.mit.edu/proxy/comments/project/{self.id}/",
            header=header,json=data
        )).json()
        return Comment(
            self.ClientSession,{"place":self,"data":resp,"id":resp["id"]},self.Session
        )



async def get_project(project_id:int,*,ClientSession=None) -> Project:
    ClientSession = common.create_ClientSession(ClientSession)
    return await base.get_object(ClientSession,project_id,Project)

def create_Partial_Project(project_id:int,author_name:"str|None"=None,*,ClientSession=None) -> Project:
    ClientSession = common.create_ClientSession(ClientSession)
    _project = Project(ClientSession,project_id)
    if author_name is not None:
        from .user import create_Partial_User
        _project.author = create_Partial_User(author_name,ClientSession=ClientSession)
    return _project


def explore_projects(*, query:str="*", mode:str="trending", language:str="en", limit:int=40, offset:int=0,ClientSession:common.Requests=None) -> AsyncGenerator["Project",None]:
    ClientSession = common.create_ClientSession(ClientSession)
    return base.get_object_iterator(
        ClientSession, f"https://api.scratch.mit.edu/explore/projects",
        None,Project,limit=limit,offset=offset,
        add_params={"language":language,"mode":mode,"q":query}
    )

def search_projects(query:str, *, mode:str="trending", language:str="en", limit:int=40, offset:int=0,ClientSession:common.Requests=None) -> AsyncGenerator["Project",None]:
    ClientSession = common.create_ClientSession(ClientSession)
    return base.get_object_iterator(
        ClientSession, f"https://api.scratch.mit.edu/search/projects",
        None,Project,limit=limit,offset=offset,
        add_params={"language":language,"mode":mode,"q":query}
    )