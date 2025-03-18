from abc import ABC, abstractmethod
import asyncio
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Literal, TypeVar
import random
import warnings

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
            update_type:Literal["get","post","put","delete"],update_url:str,
            ClientSession:common.ClientSession,
            Session:"Scratch_Session|None"=None) -> None:
        self._ClientSession:common.ClientSession = ClientSession
        self.update_type:Literal["get","post","put","delete"] = update_type
        self.update_url:str = update_url
        self._Session:"Scratch_Session|None" = Session
        self._raw:dict|str|None = None

    async def update(self) -> None:
        if self.update_type == "get": func = self.ClientSession.get
        if self.update_type == "post": func = self.ClientSession.post
        if self.update_type == "put": func = self.ClientSession.put
        if self.update_type == "delete": func = self.ClientSession.delete
        response = (await func(self.update_url,timeout=10)).json()
        if not isinstance(response,dict):
            raise self.raise_class(self.__class__,TypeError)
        self._raw = response.copy()
        return self._update_from_dict(response)
    
    @abstractmethod
    def _update_from_dict(self, data) -> None:
        pass

    @property
    def has_session(self) -> bool:
        from .session import Session as Scratch_Session
        if isinstance(self.Session,Scratch_Session):
            return True
        return False
    
    @property
    def ClientSession(self) -> common.ClientSession:
        return self._ClientSession
    
    @property
    def Session(self) -> "Scratch_Session|None":
        return self._Session
        
    def has_session_raise(self):
        if not self.has_session:
            raise exception.NoSession()
        
    async def link_session(self,session:"Scratch_Session",if_close:bool=False) -> "Scratch_Session|None":
        if if_close:
            await self.session_close()
        old_session = self.Session
        self._Session = session
        self._ClientSession = session.ClientSession
        return old_session
    
    async def session_close(self) -> None:
        await self.ClientSession.close()

    @property
    def session_closed(self) -> bool:
        return self.ClientSession.closed
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.session_close()
        return
    
_T = TypeVar("_T",_BaseSiteAPI,Any)

async def get_object(
        ClientSession:common.ClientSession|None,
        id:Any,Class:type[_T],
        session:"Scratch_Session|None"=None
    ) -> _T:
    if ClientSession is None: if_close = True
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
        if if_close: await ClientSession.close()
        raise Class.raise_class(Class,e)
    except Exception as e:
        if if_close: await ClientSession.close()
        raise exception.ObjectFetchError(Class,e)


async def get_object_iterator(
        ClientSession:common.ClientSession,
        url:str,raw_name:str|None,
        Class:type[_T],
        session:"Scratch_Session|None"=None,
        *,
        limit:int|None=None,
        offset:int=0,
        max_limit=40,
        add_params:dict={}
    ) -> AsyncGenerator[_T,None]:
    c = 0
    limit = max_limit if limit is None else limit
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
        for j in l:
            c = c + 1
            if c == limit: return
            try:
                dicts = {
                    "ClientSession":ClientSession,
                    Class.id_name:j[raw_name],
                    "scratch_session":session
                }
                _obj = Class(**dicts)
                _obj._update_from_dict(j)
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
    limit = max_limit if limit is None else limit
    for i in range(offset,offset+limit,max_limit):
        l = await common.api_iterative(
            plece.ClientSession,url,
            limit=max_limit,offset=i,max_limit=max_limit,
            add_params=add_params
        )
        if len(l) == 0:
            return
        for j in l:
            try:
                dicts = {
                    "ClientSession":plece.ClientSession,
                    "data":{
                        "place":plece,
                        "id":j.get("id"),
                        "data":j
                    },
                    "_session":plece.Session
                }
                _obj = Comment(**dicts)
                yield _obj
            except Exception as e:
                print(e)

_S = TypeVar("_S")

async def _req(func,**d) -> list:
    try:
        return [i async for i in func(**d)]
    except Exception as e:
        warnings.warn(str(e))
        return []


async def get_list_data(func:Callable[... ,AsyncGenerator[_S,None]],limit:int=40,offset:int=0,**d) -> list[_S]:
    tasks = [asyncio.create_task(_req(func,**({"limit":40,"offset":i}|d))) for i in range(offset,limit+offset,40)]
    r:list[list[_S]] = await asyncio.gather(*tasks)
    returns:list[_S] = []
    for i in r:
        returns = returns + i
    return returns[:limit]

async def get_page_list_data(func:Callable[... ,AsyncGenerator[_T,None]],start_page:int=1,end_page:int=1,**d) -> list[_T]:
    tasks = [asyncio.create_task(_req(func,**({"start_page":i,"end_page":i}|d))) for i in range(start_page,end_page+1)]
    r:list[list[_T]] = await asyncio.gather(*tasks)
    returns:list[_T] = []
    for i in r:
        returns = returns + i
    return returns

async def get_count(ClientSession:common.ClientSession,url,text_before:str, text_after:str) -> int:
    resp = await ClientSession.get(url)
    r = common.split_int(resp.text, text_before, text_after) 
    if isinstance(r,int):
        return r
    raise exception.BadResponse(resp.status_code,resp)