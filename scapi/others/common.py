import datetime
import os
from typing import Any, AsyncGenerator, Awaitable, Callable, Literal, overload, TYPE_CHECKING, TypeVar
import aiofiles
import aiohttp
from multidict import CIMultiDictProxy, CIMultiDict
from . import error as exceptions
import json
import io
import random
import string
import urllib.parse

_T = TypeVar("_T")

if TYPE_CHECKING:
    from ..sites import session

__version__ = "2.1.1"

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
    "x-csrftoken": "a",
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://scratch.mit.edu",
}

def create_ClientSession(inp:"ClientSession|None"=None,Session:"session.Session|None"=None) -> "ClientSession":

    if inp is not None:
        return inp
    elif Session is not None:
        return Session.ClientSession


    return ClientSession(header=headers,cookie={"scratchcsrftoken": 'a'},protect=True)

def create_custom_ClientSession(header:dict={},cookie:dict={}) -> "ClientSession":
    return ClientSession(header=header,cookie=cookie)

json_resp = dict[str,"json_resp"]|list["json_resp"]|str|float|int|bool|None
class Response:
    def __repr__(self) -> str:
        return f"<Response [{self.status_code}] {len(self.data)}>"

    def __init__(self,response:aiohttp.ClientResponse,text:bytes) -> None:
        self._response:aiohttp.ClientResponse = response
        self.status_code:int = response.status
        self.data:bytes = text
        self.headers:CIMultiDict[str] = response.headers.copy()
        self._encodeing:str = response.get_encoding()
        self.url:str = str(response.url)

    @property
    def text(self) -> str:
        return self.data.decode(encoding=self._encodeing)

    def json(self) -> json_resp:
        return json.loads(self.text)

class ClientSession(aiohttp.ClientSession):
    def __repr__(self):
        return f"<ClientSession protect:{self.protect} proxy:{self._proxy}>"

    def __init__(self,header:dict={},cookie:dict={},protect:bool=False) -> None:
        super().__init__()
        self._header = header
        self._cookie = cookie
        self._proxy = None
        self._proxy_auth = None
        self.protect = protect
    
    @property
    def header(self) -> dict:
        return self._header.copy()
    
    @property
    def cookie(self) -> dict:
        return self._cookie.copy()
    
    @property
    def proxy(self) -> tuple[str|None,aiohttp.BasicAuth|None]:
        return self._proxy, self._proxy_auth
    
    def set_proxy(self,url:str|None=None,auth:aiohttp.BasicAuth|None=None):
        self._proxy = url
        self._proxy_auth = auth
    
    async def _check(self,response:Response) -> None:
        if response.url.startswith("https://scratch.mit.edu/ip_ban_appeal"):
            raise exceptions.IPBanned(response)
        if response.url.startswith("https://scratch.mit.edu/accounts/banned-response"):
            raise exceptions.AccountBrocked(response)
        if response.url.startswith("https://scratch.mit.edu/accounts/login/"):
            raise exceptions.Unauthorized(response)
        if response.status_code in [403,401]:
            raise exceptions.Unauthorized(response)
        if response.status_code in [429]:
            raise exceptions.TooManyRequests(response)
        if response.status_code in [404]:
            raise exceptions.HTTPNotFound(response)
        if response.status_code // 100 == 4:
            raise exceptions.BadRequest(response)
        if response.status_code // 100 == 5:
            raise exceptions.ServerError(response)
        try:
            if response.text.startswith('{"code":"BadRequest"'):
                raise exceptions.BadResponse(response)
        except UnicodeDecodeError:
            pass

    async def _send_requests(
        self,obj:Callable[...,aiohttp.ClientResponse],url:str,*,
        data:Any=None,json:dict|None=None,timeout:float|None=None,params:dict[str,str]|None=None,
        header:dict[str,str]|None=None,cookie:dict[str,str]|None=None,check:bool=True,**d
    ) -> Response:
        if self.closed: raise exceptions.SessionClosed
        is_scratch = split(url,"//","/").lower().endswith("scratch.mit.edu")
        if self.protect and (not is_scratch):
            if header is None: header = headers
        else:
            if header is None: header = self._header.copy()
            if cookie is None: cookie = self._cookie.copy()
        try:
            async with obj(
                url,data=data,json=json,timeout=timeout,params=params,headers=header,cookies=cookie,
                proxy=self._proxy,proxy_auth=self._proxy_auth,**d
            ) as response:
                r = Response(response,await response.read())
                #print("\n".join([str(r),str(data or json),r.url,r.text[:2000],str(r)]))
                response.close()
        except Exception as e:
            raise exceptions.HTTPFetchError(e)
        if check: await self._check(r)
        return r

    async def get(
        self,url:str,*,
        data:Any=None,json:dict|None=None,timeout:float|None=None,params:dict[str,str]|None=None,
        header:dict[str,str]|None=None,cookie:dict[str,str]|None=None,check:bool=True,**d
    ) -> Response:
        return await self._send_requests(
            super().get,url=url,
            data=data,json=json,timeout=timeout,params=params,
            header=header,cookie=cookie,check=check,**d
        )
    
    async def post(
        self,url:str,*,
        data:Any=None,json:dict|None=None,timeout:float|None=None,params:dict[str,str]|None=None,
        header:dict[str,str]|None=None,cookie:dict[str,str]|None=None,check:bool=True,**d
    ) -> Response:
        return await self._send_requests(
            super().post,url=url,
            data=data,json=json,timeout=timeout,params=params,
            header=header,cookie=cookie,check=check,**d
        )

    async def put(
        self,url:str,*,
        data:Any=None,json:dict|None=None,timeout:float|None=None,params:dict[str,str]|None=None,
        header:dict[str,str]|None=None,cookie:dict[str,str]|None=None,check:bool=True,**d
    ) -> Response:
        return await self._send_requests(
            super().put,url=url,
            data=data,json=json,timeout=timeout,params=params,
            header=header,cookie=cookie,check=check,**d
        )

    async def delete(
        self,url:str,*,
        data:Any=None,json:dict|None=None,timeout:float|None=None,params:dict[str,str]|None=None,
        header:dict[str,str]|None=None,cookie:dict[str,str]|None=None,check:bool=True,**d
    ) -> Response:
        return await self._send_requests(
            super().delete,url=url,
            data=data,json=json,timeout=timeout,params=params,
            header=header,cookie=cookie,check=check,**d
        )
    
    async def __aenter__(self):
        return self



async def api_iterative(
        session:ClientSession,
        url:str,
        *,
        limit:int|None=None,
        offset:int=0,
        max_limit=40,
        is_page:bool=False,
        add_params:dict[str,str]={}
    ) -> list[dict]:
    """
    APIを叩いてリストにして返す
    """
    if offset < 0:
        raise ValueError("offset parameter must be >= 0")
    if limit is None:
        limit = max_limit
    if limit < 0:
        raise ValueError("limit parameter must be >= 0")
    if is_page:
        params = {"page":str(offset)}
    else:
        params = {"limit":str(limit),"offset":str(offset)}

    r = await session.get(
        url,timeout=10,
        params=params|add_params
    )
    jsons = r.json()
    if not isinstance(jsons,list):
        raise exceptions.BadResponse(r)
    return jsons



def split_int(raw:str, text_before:str, text_after:str) -> int|None:
    try:
        return int(raw.split(text_before)[1].split(text_after)[0])
    except Exception:
        return None
    
def split(raw:str, text_before:str, text_after:str) -> str:
    try:
        return raw.split(text_before)[1].split(text_after)[0]
    except Exception:
        return ""
    
    
def to_dt(text:str,default:_T=None) -> datetime.datetime|_T:
    try:
        return datetime.datetime.fromisoformat(f'{text.replace("Z","")}+00:00')
    except Exception:
        return default
    
def to_dt_timestamp_1000(text:int,default:_T=None) -> datetime.datetime|_T:
    try:
        return datetime.datetime.fromtimestamp(text/1000,tz=datetime.timezone.utc)
    except Exception:
        return default
    
def no_data_checker(obj) -> None:
    if obj is None:
        raise exceptions.NoDataError
    
def try_int(inp:str|int) -> int:
    try:
        return int(inp)
    except Exception:
        raise ValueError
    
async def downloader(
    clientsession:ClientSession,url:str,download_path:str
):
    r = await clientsession.get(url)
    async with aiofiles.open(download_path,"bw") as f:
        await f.write(r.data)

async def open_tool(inp:str|bytes,default_filename:str) -> tuple[bytes, str]:
    if isinstance(inp,str):
        async with aiofiles.open(inp,"br") as f:
            return await f.read(), os.path.basename(inp)
    elif isinstance(inp,bytes):
        return inp,default_filename
    raise TypeError

def get_id(obj:Any,name:str="id") -> int|str|None:
    if obj is None:
        return None
    if isinstance(obj,(int,str)):
        return obj
    r = getattr(obj,name)
    if r is None:
        raise exceptions.NoDataError()
    return r

empty_project_json = {
    'targets': [
        {
            'isStage': True,
            'name': 'Stage',
            'variables': {
                '`jEk@4|i[#Fk?(8x)AV.-my variable': [
                    'my variable',
                    0,
                ],
            },
            'lists': {},
            'broadcasts': {},
            'blocks': {},
            'comments': {},
            'currentCostume': 0,
            'costumes': [
                {
                    'name': '',
                    'bitmapResolution': 1,
                    'dataFormat': 'svg',
                    'assetId': '14e46ec3e2ba471c2adfe8f119052307',
                    'md5ext': '14e46ec3e2ba471c2adfe8f119052307.svg',
                    'rotationCenterX': 0,
                    'rotationCenterY': 0,
                },
            ],
            'sounds': [],
            'volume': 100,
            'layerOrder': 0,
            'tempo': 60,
            'videoTransparency': 50,
            'videoState': 'on',
            'textToSpeechLanguage': None,
        },
    ],
    'monitors': [],
    'extensions': [],
    'meta': {
        'semver': '3.0.0',
        'vm': '2.3.0',
        'agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    },
}

BIG = 99999999

async def do_nothing(*l,**d):
    return

def deprecated(class_name:str,old:str,new:str) -> Callable[[_T], _T]:
    def inner(f:_T) -> _T:
        def deprecated_func(*l,**d):
            print(f"Function {old} in class {class_name} is deprecated."
                  f"\nUse the new {new} function")
            return f(*l,**d)
        return deprecated_func
    return inner
