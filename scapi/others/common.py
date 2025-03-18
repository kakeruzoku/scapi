import datetime
import os
from typing import Any, AsyncGenerator, Awaitable, Callable, Literal, overload
import aiofiles
import aiohttp
from multidict import CIMultiDictProxy, CIMultiDict
from . import error as exceptions
import json

__version__ = "1.1.1"

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
    "x-csrftoken": "a",
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://scratch.mit.edu",
}

def create_ClientSession(inp:"ClientSession|None"=None,*,proxy=None) -> "ClientSession":
    if isinstance(inp,ClientSession):
        if proxy is None:
            return inp


    return inp if isinstance(inp,ClientSession) else ClientSession(header=headers,cookie={"scratchcsrftoken": 'a'})

def create_custom_ClientSession(header:dict={},cookie:dict={}) -> "ClientSession":
    return ClientSession(header=header,cookie=cookie)

json_resp = dict[str,"json_resp"]|list["json_resp"]|str|float|int|bool|None
class Response:
    def __str__(self) -> str:
        return f"<Response [{self.status_code}] {self.text}>"

    def __init__(self,status:int,text:bytes,headers:CIMultiDictProxy[str],encodeing:str) -> None:
        self.status_code:int = status
        self.data:bytes = text
        self.headers:CIMultiDict[str] = headers.copy()
        self._encodeing:str = encodeing

    @property
    def text(self) -> str:
        return self.data.decode(encoding=self._encodeing)

    def json(self) -> json_resp:
        return json.loads(self.text)

class ClientSession(aiohttp.ClientSession):

    def __init__(self,header:dict={},cookie:dict={}) -> None:
        super().__init__()
        self._header = header
        self._cookie = cookie
        self._proxy = None
        self._proxy_auth = None
    
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
        if response.status_code in [403,401]:
            raise exceptions.Unauthorized(response.status_code,response)
        if response.status_code in [429]:
            raise exceptions.TooManyRequests(response.status_code,response)
        if response.status_code in [404]:
            raise exceptions.HTTPNotFound(response.status_code,response)
        if response.status_code // 100 == 4:
            raise exceptions.BadRequest(response.status_code,response)
        if response.status_code // 100 == 5:
            raise exceptions.ServerError(response.status_code,response)
        if isinstance(response,Response):
            if response.text == '{"code":"BadRequest","message":""}':
                raise exceptions.BadResponse(response.status_code,response)

    async def _send_requests(
        self,obj:Callable[...,aiohttp.ClientResponse],url:str,*,
        data:Any=None,json:dict|None=None,timeout:float|None=None,params:dict[str,str]|None=None,
        header:dict[str,str]|None=None,cookie:dict[str,str]|None=None,check:bool=True,**d
    ) -> Response:
        if self.closed: raise exceptions.SessionClosed
        if header is None: header = self._header.copy()
        if cookie is None: cookie = self._cookie.copy()
        try:
            async with obj(
                url,data=data,json=json,timeout=timeout,params=params,headers=header,cookies=cookie,
                proxy=self._proxy,proxy_auth=self._proxy_auth,**d
            ) as response:
                r = Response(response.status,await response.read(),response.headers,response.get_encoding())
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



async def api_iterative(
        session:ClientSession,
        url:str,
        *,
        limit:int|None=None,
        offset:int=0,
        max_limit=40,
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
    
    r = await session.get(
        url,timeout=10,
        params=dict(limit=str(limit),offset=str(offset),**add_params)
    )
    jsons = r.json()
    if not isinstance(jsons,list):
        raise exceptions.HTTPError()
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
    
def to_dt(text:str,default:datetime.datetime|None=None) -> datetime.datetime|None:
    try:
        return datetime.datetime.fromisoformat(f'{text.replace("Z","")}+00:00')
    except Exception:
        return default
    
def to_dt_timestamp_1000(text:int,default:datetime.datetime|None=None) -> datetime.datetime|None:
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
        if inp.endswith("/"): inp = inp[:-1]
        async with aiofiles.open(inp,"br") as f:
            return await f.read(), inp.split("/")[-1]
    elif isinstance(inp,bytes):
        return inp,default_filename
    raise TypeError

async def requests_with_file(filedata:bytes,filename:str,url:str,clientsession:ClientSession) -> Response:
    filename = filename.replace("\\","/")
    if filename.endswith("/"): filename = filename[:-1]
    filename = filename.split("/")[-1]
    Extension = filename.split(".")[-1]
    before = f'------WebKitFormBoundaryhKZwFjoxAyUTMlSh\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: image/{Extension}\r\n\r\n'.encode("utf-8")
    after = b"\r\n------WebKitFormBoundaryhKZwFjoxAyUTMlSh--\r\n"
    payload = b"".join([before,filedata,after])
    return await clientsession.post(
        url,
        data=payload,
        header=clientsession.header|{
            "accept": "*/",
            "content-type": "multipart/form-data; boundary=----WebKitFormBoundaryhKZwFjoxAyUTMlSh",
            "Referer": "https://scratch.mit.edu/",
            "x-csrftoken": "a",
            "x-requested-with": "XMLHttpRequest",
        }
    )

def get_id(obj:Any,name:str="id") -> int|str:
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
