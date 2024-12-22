from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncGenerator, Literal
import random

from ..others import common as common
from ..others import error as exception

if TYPE_CHECKING:
    from .session import Session as Scratch_Session
    from .comment import Comment
    from .studio import Studio
    from .project import Project

class _BaseSiteAPI(ABC):
    raise_class = exception.ObjectNotFound
    id_name = ""

    def __init__(
            self,
            update_type:str,update_url:str,
            ClientSession:common.Requests,
            Session:"Scratch_Session|None"=None) -> None:
        self._csid:bytes = random.randbytes(32)
        self.ClientSession:common.Requests = ClientSession
        self.update_type:Literal["get","post","put","delete"] = update_type
        self.update_url:str = update_url
        self.Session:"Scratch_Session|None" = Session
        self._raw:dict = None

    async def update(self) -> None:
        if self.update_type == "get": func = self.ClientSession.get
        if self.update_type == "post": func = self.ClientSession.post
        if self.update_type == "put": func = self.ClientSession.put
        if self.update_type == "delete": func = self.ClientSession.delete
        response:dict = (await func(self.update_url,timeout=10)).json()
        if not isinstance(response,dict):
            raise self.raise_class(self.__class__,TypeError)
        self._raw = response.copy()
        return self._update_from_dict(response)
    
    @abstractmethod
    def _update_from_dict(self, data) -> None:
        pass

    def has_session(self) -> None:
        if self.Session is None:
            raise exception.NoSession()
        
    async def link_session(self,session:"Scratch_Session",if_close:bool=True) -> None:
        if if_close:
            await self.session_close()
        self.Session = session
        self.ClientSession = session.ClientSession

    async def session_close(self) -> bool:
        await self.ClientSession.close()
        del self.ClientSession

    @property
    def session_closed(self) -> bool:
        return self.ClientSession.closed
    
    def check_closed(self) -> None:
        if self.session_closed:
            raise exception.SessionClosed

async def get_object(
        ClientSession:common.Requests|None,
        id:Any,Class:_BaseSiteAPI.__class__,
        session:"Scratch_Session|None"=None
    ) -> _BaseSiteAPI:
    ClientSession = common.create_ClientSession(ClientSession)
    try:
        dicts = {
            "ClientSession":ClientSession,
            Class.id_name:id,
            "scratch_session":session
        }
        _object = Class(**dicts)
        await _object.update()
        return _object
    except (KeyError, exception.BadRequest) as e:
        raise Class.raise_class(Class,e)
    except Exception as e:
        raise exception.ObjectFetchError(Class,e)


async def get_object_iterator(
        ClientSession:common.Requests,
        url:str,raw_name:str|None,
        Class:_BaseSiteAPI.__class__,
        session:"Scratch_Session|None"=None,
        *,
        limit:int|None=None,
        offset:int=0,
        max_limit=40,
        add_params:dict={}
    ) -> AsyncGenerator[_BaseSiteAPI,None]:
    for i in range(offset,offset+limit,max_limit):
        l = await common.api_iterative(
            ClientSession,url,
            limit=max_limit,offset=i,max_limit=max_limit,
            add_params=add_params
        )
        if len(l) == 0:
            return
        if raw_name is None:
            raw_name = Class.id_name
        for i in l:
            try:
                dicts = {
                    "ClientSession":ClientSession,
                    Class.id_name:i[raw_name],
                    "_session":session
                }
                _obj = Class(**dicts)
                _obj._update_from_dict(i)
                yield _obj
            except Exception as e:
                print(e)


async def get_comment_iterator(
        plece:"Studio|Project",url:str,
        *,
        limit:int|None=None,
        offset:int=0,
        max_limit=40,
        add_params:dict={},
    ) -> AsyncGenerator["Comment",None]:
    from .comment import Comment
    for i in range(offset,offset+limit,max_limit):
        l = await common.api_iterative(
            plece.ClientSession,url,
            limit=max_limit,offset=i,max_limit=max_limit,
            add_params=add_params
        )
        if len(l) == 0:
            return
        for i in l:
            try:
                dicts = {
                    "ClientSession":plece.ClientSession,
                    "data":{
                        "place":plece,
                        "id":i.get("id"),
                        "data":i
                    },
                    "_session":plece.Session
                }
                _obj = Comment(**dicts)
                yield _obj
            except Exception as e:
                print(e)

async def get_count(ClientSession:common.Requests,url,text_before:str, text_after:str) -> int:
    return common.split_int((await ClientSession.get(url)).text, text_before, text_after)