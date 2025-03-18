import datetime
import random
from typing import AsyncGenerator, Literal, TypedDict, TYPE_CHECKING, overload
import warnings

from ..others import  common
from ..others import error as exception
from . import base

if TYPE_CHECKING:
    from .session import Session
    from .user import User
    from .studio import Studio
    from .project import Project

class CommentData(TypedDict):
    place:"Project|Studio"
    id:int
    data:dict|None

_FALSE:bool = False

class Comment(base._BaseSiteAPI):
    raise_class = exception.CommentNotFound
    id_name = "data"

    def __str__(self):
        return f"<Comment id:{self.id} content:{self.content} place:{self.place} user:{self.author} Session:{self.Session}>"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        data:CommentData,
        scratch_session:"Session|None"=None,
        **entries
    ) -> None:
        from .user import User
        from .studio import Studio
        from .project import Project
        
        self.place:Project|Studio = data.get("place")
        self.id:int = data.get("id")
        self.type:Literal["Project"]|Literal["Studio"] = None

        if isinstance(self.place,Project):
            self.type = "Project"
            if (self.place.author is None) or _FALSE:
                super().__init__("get",f"",ClientSession,scratch_session)
            else:
                super().__init__("get",
                    f"https://api.scratch.mit.edu/users/{self.place.author.username}/projects/{self.place.id}/comments/{self.id}",
                    ClientSession,scratch_session
                )
        elif isinstance(self.place,Studio):
            self.type = "Studio"
            super().__init__("get",
                f"https://api.scratch.mit.edu/studios/{self.place.id}/comments/{self.id}",
                ClientSession,scratch_session
            )
        else:
            raise ValueError
            
        self.parent_id:int|None = None
        self.commentee_id:int|None = None
        self.content:str = None
        self.sent_dt:datetime.datetime = None
        self.author:User = None
        self.reply_count:int = None

        self._parent_cache:"Comment|None" = None
        if data.get("data",None) is not None:
            self._update_from_dict(data.get("data"))

    @property
    def _is_me(self) -> bool:
        if isinstance(self.Session,Session):
            if self.Session.username == self.author.username:
                return True
        return False
    
    def _is_me_raise(self) -> None:
        if not self._is_me:
            raise exception.NoPermission
        
    def __int__(self) -> int: return self.id
    def __eq__(self,value) -> bool: return isinstance(value,Comment) and self.id == value.id
    def __ne__(self,value) -> bool: return isinstance(value,Comment) and self.id != value.id
    def __lt__(self,value) -> bool: return isinstance(value,Comment) and self.id < value.id
    def __gt__(self,value) -> bool: return isinstance(value,Comment) and self.id > value.id
    def __le__(self,value) -> bool: return isinstance(value,Comment) and self.id <= value.id
    def __ge__(self,value) -> bool: return isinstance(value,Comment) and self.id >= value.id

    def _update_from_dict(self, data:dict) -> None:
        from .user import User
        self.parent_id = data.get("parent_id",self.parent_id)
        self.commentee_id = data.get("commentee_id",self.commentee_id)
        self.content = data.get("content",self.content)
        self.sent_dt = common.to_dt(data.get("datetime_created"),self.sent_dt)
        _author:dict = data.get("author",{})
        self.author = User(
            self.ClientSession,_author.get("username"),self.Session
        )
        self.author._update_from_dict(_author)
        self.reply_count = data.get("reply_count",self.reply_count)

    async def get_parent_comment(self,use_cache:bool=True) -> "Comment|None":
        if (self._parent_cache is not None) and (use_cache):
            return self._parent_cache
        if self.parent_id is None:
            return None
        self._parent_cache = await self.place.get_comment_by_id(self.parent_id)
        return self._parent_cache
        
    
    def get_replies(self, *, limit=40, offset=0) -> AsyncGenerator["Comment",None]:
        return base.get_comment_iterator(
            self.place,f"{self.update_url}/replies/",
            limit=limit,offset=offset,add_params={"cachebust":random.randint(0,9999)}
        )

    async def reply(self, content, *, commentee_id:"int|User|None"=None) -> "Comment":
        return await self.place.post_comment(
            content,commentee=self.author.id if commentee_id is None else commentee_id,
            parent=self.id if self.parent_id is None else self.parent_id
        )

    async def delete(self) -> bool:
        self.has_session_raise()
        if self.type == "Project":
            return (await self.ClientSession.delete(f"https://api.scratch.mit.edu/proxy/comments/project/{self.place.id}/comment/{self.id}",data="{}")).status_code == 200
        elif self.type == "Studio":
            return (await self.ClientSession.delete(f"https://api.scratch.mit.edu/proxy/comments/studio/{self.place.id}/comment/{self.id}",data="{}")).status_code == 200
        raise TypeError()

    async def report(self) -> bool:
        self.has_session_raise()
        if self.type == "Project":
            return (await self.ClientSession.post(f"https://api.scratch.mit.edu/proxy/project/{self.place.id}/comment/{self.id}/report",json={"reportId":None})).status_code == 200
        elif self.type == "Studio":
            return (await self.ClientSession.post(f"https://api.scratch.mit.edu/proxy/studio/{self.place.id}/comment/{self.id}/report",json={"reportId":None})).status_code == 200
        raise TypeError()

class UserComment(Comment):
    def __init__(self,user,ClientSession:common.ClientSession,scratch_session:"Session|None"=None):
        self._ClientSession:common.ClientSession = ClientSession
        self.update_type = ""
        self.update_url = ""
        self._Session:Session|None = scratch_session
        self._raw = None

        self.place:User = user
        self.id:int = None
        self.type:Literal["User"] = "User"

        self.parent_id:int|None = None
        self.commentee_id:int|None = None
        self.content:str = None
        self.sent_dt:datetime.datetime = None
        self.author:User = None
        self.reply_count:int = None

        self._parent_cache:"UserComment|None" = None
        self._reply_cache:"list[UserComment]" = None
        self.page:int = 1
        
    async def update(self):
        r = await self.place.get_comment_by_id(self.id,self.page)
        self.parent_id = r.parent_id
        self.commentee_id = r.commentee_id
        self.content = r.content
        self.sent_dt = r.sent_dt
        self.author = r.author
        self.reply_count = r.reply_count
        self._parent_cache = r._parent_cache
        self._reply_cache = r._reply_cache

    def _update_from_dict(self, data:dict) -> None:
        super()._update_from_dict(data)
        self._reply_cache = data.get("_reply_cache",[])
        self.id = data.get("id")
        self._parent_cache = data.get("_parent_cache",None)
        self.page = data.get("page",self.page)

    async def get_replies(self, *, limit=40, offset=0) -> AsyncGenerator["UserComment",None]:
        for i in self._reply_cache[offset:offset+limit]:
            yield i

    async def reply(self, content, *, commentee_id=None) -> "UserComment":
        return await self.place.post_comment(
            content,commentee=self.author.id if commentee_id is None else commentee_id,
            parent=self.id if self.parent_id is None else self.parent_id
        )

    async def delete(self) -> bool:
        return (await self.ClientSession.post(
            f"https://scratch.mit.edu/site-api/comments/user/{self.place.username}/del/",
            json={"id":str(self.id)})).status_code == 200
    
    async def report(self) -> bool:
        self.has_session_raise()
        return (await self.ClientSession.post(
            f"https://scratch.mit.edu/site-api/comments/user/{self.place.username}/rep/",
            json={"id":str(self.id)})).status_code == 200

@overload
def create_Partial_Comment(comment_id:int,place:"Project|Studio",content:str|None=None,author:"User|None"=None,*,ClientSession:common.ClientSession|None=None,session:"Session|None"=None) -> Comment: ...

@overload
def create_Partial_Comment(comment_id:int,place:"User",content:str|None=None,author:"User|None"=None,*,ClientSession:common.ClientSession|None=None,session:"Session|None"=None) -> UserComment: ...


def create_Partial_Comment(comment_id:int,place:"Project|Studio|User",content:str|None=None,author:"User|None"=None,*,ClientSession:common.ClientSession|None=None,session:"Session|None"=None) -> Comment|UserComment:
    from .user import User
    from .studio import Studio
    from .project import Project
    ClientSession = common.create_ClientSession(ClientSession)
    if isinstance(place, (Project,Studio)):
        _comment = Comment(ClientSession,{"place":place,"id":comment_id},session)
    elif isinstance(place, User):
        _comment = UserComment(place,ClientSession,session)
    else:
        raise ValueError
    _comment.id = comment_id
    _comment.author = author
    _comment.content = content
    return _comment


