import datetime
import json
import random
from typing import AsyncGenerator, TYPE_CHECKING, Literal, TypedDict
import aiohttp


from ..others import common as common
from ..others import error as exception
from . import base,activity,comment
from . import project

if TYPE_CHECKING:
    from .session import Session
    from . import user,classroom
    from ..event.comment import CommentEvent

class Studio(base._BaseSiteAPI):
    id_name = "id"

    def __repr__(self):
        return f"<Studio id:{self.id} title:{self.title} Session:{self.Session}>"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        id:int,
        scratch_session:"Session|None"=None,
        **entries
    ):
        super().__init__("get",f"https://api.scratch.mit.edu/studios/{id}",ClientSession,scratch_session)

        self.id:int = common.try_int(id)
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
        self.comment_count:int = None
        self.curator_count:int|None = None

    def _update_from_dict(self, data:dict):
        self.title = data.get("title",self.title)
        self.description = data.get("description",self.description)
        self.author_id = data.get("host",self.author_id)

        self.open_to_all = data.get("open_to_all",self.open_to_all)
        self.comments_allowed = data.get("comments_allowed",self.comments_allowed)

        _history:dict = data.get("history",{})
        self._add_datetime("created",_history.get("created"))
        self._add_datetime("modified",_history.get("modified"))

        _stats:dict = data.get("stats",{})
        self.follower_count = _stats.get("followers",self.follower_count)
        self.manager_count = _stats.get("managers",self.manager_count)
        self.project_count = _stats.get("projects",self.project_count)
        self.comment_count = _stats.get("comments",self.comment_count)

    def _update_from_old_dict(self, fields:dict):
        from . import user
        self.curator_count = fields.get("curators_count",self.curator_count)
        self.project_count = fields.get("projecters_count",self.project_count)
        self.title = fields.get("title",self.title)
        self._add_datetime("created",fields.get("datetime_created"))
        self.comment_count = fields.get("commenters_count",self.comment_count)
        self._add_datetime("modified",fields.get("datetime_modified"))

        _author:dict = fields.get("owner")
        self.author = user.User(self.ClientSession,_author.get("username",self.Session.username),self.Session)
        self.author.id = _author.get("pk",self.Session.status.id)
        self.author.scratchteam = _author.get("admin",self.Session.status.admin)
    
    def _update_from_mystuff(self, data:dict):
        self._update_from_old_dict(data.get("fields"))

    @property
    def image_url(self) -> str:
        return f"https://cdn2.scratch.mit.edu/get_image/gallery/{self.id}_170x100.png"
    
    @property
    def url(self) -> str:
        return f"https://scratch.mit.edu/studios/{self.id}/"
    
    @property
    def _is_owner(self) -> bool:
        from .session import Session
        if isinstance(self.Session,Session):
            if self.Session.status.id == self.author_id:
                return True
        return False
    
    def _is_owner_raise(self) -> None:
        if self.check and not self._is_owner:
            raise exception.NoPermission

    def __int__(self) -> int: return self.id
    def __eq__(self,value) -> bool: return isinstance(value,Studio) and self.id == value.id
    def __ne__(self,value) -> bool: return isinstance(value,Studio) and self.id != value.id
    def __lt__(self,value) -> bool: return isinstance(value,Studio) and self.id < value.id
    def __gt__(self,value) -> bool: return isinstance(value,Studio) and self.id > value.id
    def __le__(self,value) -> bool: return isinstance(value,Studio) and self.id <= value.id
    def __ge__(self,value) -> bool: return isinstance(value,Studio) and self.id >= value.id

    
    async def get_comment_by_id(self,id:int,is_old:bool|None=None) -> comment.Comment:
        is_old = bool(is_old)

        if is_old:
            return await comment._get_comment_old_api_by_id(self,f"https://scratch.mit.edu/site-api/comments/gallery/{self.id}",id)
        else:
            return await base.get_object(
                self.ClientSession,id,comment.Comment,self.Session,base._comment_get_func,others={"plece":self}
            )
    
    def get_comments(self, *, limit:int=40, offset:int=0, start_page:int=1, end_page:int=1, is_old:bool|None=None) -> AsyncGenerator[comment.Comment, None]:
        is_old = bool(is_old)

        if is_old:
            return comment._get_comments_old_api(self,f"https://scratch.mit.edu/site-api/comments/gallery/{self.id}",start_page=start_page,end_page=end_page)
        else:
            return base.get_object_iterator(
                self.ClientSession,f"https://api.scratch.mit.edu/studios/{self.id}/comments",None,comment.Comment,
                limit=limit,offset=offset,add_params={"cachebust":random.randint(0,9999)},
                custom_func=base._comment_iterator_func, others={"plece":self}
            )
    
    async def post_comment(self, content:str, parent:int|comment.Comment|None=None, commentee:"int|user.User|None"=None, is_old:bool|None=None) -> comment.Comment:
        self.has_session_raise()

        if is_old is None: is_old = False
        if is_old: url = f"https://scratch.mit.edu/site-api/comments/gallery/{self.id}/add/"
        else: url = f"https://api.scratch.mit.edu/proxy/comments/studio/{self.id}/"

        return await comment._post_comment(
            self,url,is_old,content,common.get_id(commentee),common.get_id(parent)
        )
    
    def comment_event(self,interval=30) -> "CommentEvent":
        from ..event.comment import CommentEvent
        return CommentEvent(self,interval)
    
    async def follow(self,follow:bool) -> None:
        # This API 's response == Session.me.featured_data() wtf??????????
        self.has_session_raise()
        if follow:
            self.ClientSession.put(f"https://scratch.mit.edu/site-api/users/bookmarkers/{self.id}/add/?usernames={self.Session.username}")
        else:
            self.ClientSession.put(f"https://scratch.mit.edu/site-api/users/bookmarkers/{self.id}/remove/?usernames={self.Session.username}")

    async def set_thumbnail(self,thumbnail:bytes|str,filename:str="image.png"):
        self._is_owner_raise()
        thumbnail,filename = await common.open_tool(thumbnail,filename)
        form = aiohttp.FormData()
        form.add_field("file",thumbnail,filename=filename)
        await self.ClientSession.post(f"https://scratch.mit.edu/site-api/galleries/all/{self.id}/",data=form)
    
    async def edit(
            self,
            title:str|None=None,
            description:str|None=None,
            trash:bool|None=None
        ) -> None:
        data = {}
        self._is_owner_raise()
        if description is not None: data["description"] = description + "\n"
        if title is not None: data["title"] = title
        if trash: data["visibility"] = "delbyusr"
        r = await self.ClientSession.put(f"https://scratch.mit.edu/site-api/galleries/all/{self.id}",json=data)
        self._update_from_dict(r.json())

    async def open_adding_project(self,is_open:bool=True):
        self.has_session_raise()
        if is_open:
            r = await self.ClientSession.put(f"https://scratch.mit.edu/site-api/galleries/{self.id}/mark/open/")
        else:
            r = await self.ClientSession.put(f"https://scratch.mit.edu/site-api/galleries/{self.id}/mark/closed/")
        if r.json().get("success",False):
            return
        raise exception.BadResponse(r)
        
    async def open_comment(self,is_open:bool=True,is_update:bool=False):
        self._is_owner_raise()
        if is_update: await self.update()
        if self.comments_allowed != is_open:
            r = await self.ClientSession.post(f"https://scratch.mit.edu/site-api/comments/gallery/{self.id}/toggle-comments/")
            if r.text == "ok":
                self.comments_allowed = is_open
                return
            raise exception.BadResponse(r)
        return

    async def invite(self,username:"str|user.User"):
        self.has_session_raise()
        r = await self.ClientSession.put(f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/invite_curator/?usernames={common.get_id(username,"username")}")
        if r.json().get("status","error") != "success":
            raise exception.BadResponse(r)
    
    async def accept_invite(self):
        self.has_session_raise()
        r = await self.ClientSession.put(f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/add/?usernames={self.Session.username}")
        if not r.json().get("success",False):
            raise exception.BadResponse(r)
    
    async def promote(self,username:"str|user.User"): #404
        self.has_session_raise()
        await self.ClientSession.put(f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/promote/?usernames={common.get_id(username,'username')}")
    
    async def remove_user(self,username:"str|user.User"): #404
        self.has_session_raise()
        await self.ClientSession.put(f"https://scratch.mit.edu/site-api/users/curators-in/{self.id}/remove/?usernames={common.get_id(username,'username')}")
    
    async def transfer_ownership(self,username:"str|user.User",password:str) -> None:
        self._is_owner_raise()
        await self.ClientSession.put(
            f"https://api.scratch.mit.edu/studios/{self.id}/transfer/{common.get_id(username,'username')}",
            json={"password":password}
        )

    async def leave(self):
        self.has_session_raise()
        return await self.remove_user(self.Session.username)

    async def add_project(self,project_id:int|project.Project):
        self.has_session_raise()
        await self.ClientSession.post(f"https://api.scratch.mit.edu/studios/{self.id}/project/{common.get_id(project_id)}")

    async def remove_project(self,project_id:int|project.Project):
        self.has_session_raise()
        await self.ClientSession.delete(f"https://api.scratch.mit.edu/studios/{self.id}/project/{common.get_id(project_id)}")
    
    def projects(self, *, limit=40, offset=0) -> AsyncGenerator[project.Project, None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/studios/{self.id}/projects",
            None,project.Project,self.Session,
            limit=limit,offset=offset
        )
    
    def curators(self, *, limit=40, offset=0) -> AsyncGenerator["user.User", None]:
        from . import user
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/studios/{self.id}/curators",
            None,user.User,self.Session,
            limit=limit,offset=offset
        )
    
    def managers(self, *, limit=40, offset=0) -> AsyncGenerator["user.User", None]:
        from . import user
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/studios/{self.id}/managers",
            None,user.User,self.Session,
            limit=limit,offset=offset
        )
    
    async def host(self) -> "user.User":
        return [i async for i in self.managers(limit=10)][0]
    
    async def activity(self, *, limit=40, datelimit:datetime.datetime|None=None) -> AsyncGenerator[activity.Activity, None]:
        c = 0
        dt = str(datetime.datetime.now(datetime.timezone.utc) if datelimit is None else datelimit.astimezone(datetime.timezone.utc))
        for _ in range(0,limit,40):
            r = await common.api_iterative(
                self.ClientSession,f"https://api.scratch.mit.edu/studios/{self.id}/activity",limit=40,
                add_params={"dateLimit":dt.replace("+00:00","Z")}
            )
            if len(r) == 0: return
            for j in r:
                _obj = activity.Activity()
                _obj._update_from_studio(self,j)
                dt = str(_obj.datetime - datetime.timedelta(seconds=1))
                yield _obj
                c = c + 1
                if c == limit: return

    class studio_roles(TypedDict):
        manager:bool
        curator:bool
        invited:bool
        following:bool

    async def roles(self) -> studio_roles:
        self.has_session_raise()
        return (await self.ClientSession.get(
            f"https://api.scratch.mit.edu/studios/{self.id}/users/{self.Session.username}",
        )).json()
    
    async def classroom(self) -> "classroom.Classroom|None":
        from . import classroom
        r = await self._classroom()
        if r is None:
            return r
        return await base.get_object(self.ClientSession,r,classroom.Classroom,self.Session)

    async def _classroom(self) -> int|None:
        try:
            r = await self.ClientSession.get(f"https://api.scratch.mit.edu/studios/{self.id}/classroom")
            return r.json().get("id")
        except exception.HTTPNotFound:
            return None
    
    async def report(self,type:Literal["title","description","thumbnail"]):
        self.has_session_raise()
        r = await self.ClientSession.post(
            f"https://scratch.mit.edu/site-api/galleries/all/{self.id}/report/",
            data=f"selected_field={type}"
        )
        if len(r.text) == 0:
            raise exception.BadResponse(r)
        if not r.json().get("success"):
            raise exception.BadResponse(r)
        return

    
async def get_studio(studio_id:int,*,ClientSession=None) -> Studio:
    return await base.get_object(ClientSession,studio_id,Studio)

def create_Partial_Studio(studio_id:int,*,ClientSession:common.ClientSession|None=None,session:"Session|None"=None) -> Studio:
    ClientSession = common.create_ClientSession(ClientSession)
    return Studio(ClientSession,studio_id,session)

def explore_studios(*, query:str="*", mode:str="trending", language:str="en", limit:int=40, offset:int=0,ClientSession:common.ClientSession|None=None) -> AsyncGenerator["Studio",None]:
    return base.get_object_iterator(
        ClientSession, "https://api.scratch.mit.edu/explore/studios",
        None,Studio,limit=limit,offset=offset,
        add_params={"language":language,"mode":mode,"q":query}
    )

def search_studios(query:str, *, mode:str="trending", language:str="en", limit:int=40, offset:int=0,ClientSession:common.ClientSession|None=None) -> AsyncGenerator["Studio",None]:
    return base.get_object_iterator(
        ClientSession, "https://api.scratch.mit.edu/search/studios",
        None,Studio,limit=limit,offset=offset,
        add_params={"language":language,"mode":mode,"q":query}
    )