from typing import Any, Callable, TypedDict, Unpack
import aiohttp
import json as _json
from urllib.parse import urlparse
from . import error,common

default_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
    "x-csrftoken": "a",
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://scratch.mit.edu",
}

default_proxy:str|None=None
default_proxy_auth:aiohttp.BasicAuth|None=None

def set_default_proxy(url:str|None=None,auth:aiohttp.BasicAuth|None=None):
    global default_proxy,default_proxy_auth
    default_proxy = url
    default_proxy_auth = auth

class _RequestOptions(TypedDict, total=False):
    params: dict[str,str|int|float]
    data: Any
    json: Any
    cookies: dict[str,str]|None
    headers: dict[str,str]|None
    check: bool

class Response:
    def __init__(self,response:aiohttp.ClientResponse):
        self._response = response
        self.status_code:int = response.status
        assert response._body
        self._body = response._body

    @property
    def data(self) -> bytes:
        return self._body
    
    @property
    def text(self) -> str:
        return self._body.decode(self._response.get_encoding())
    
    def json(self,loads:Callable[[str], Any]=_json.loads,/,**kwargs) -> Any:
        return loads(self.text,**kwargs)
    
    def json_or_text(self,loads:Callable[[str], Any]=_json.loads,/,**kwargs) -> Any:
        try:
            return self.json(loads,**kwargs)
        except Exception:
            return self.text

class HTTPClient:
    def __init__(
            self,*,
            headers:dict[str,str]|None=None,
            cookies:dict[str,str]|None=None,
            scratch_cookies:dict[str,str]|None=None
        ):
        self.headers = headers or default_headers
        self.cookies = cookies or {}
        self.scratch_cookies = scratch_cookies or {}
        self._proxy = default_proxy
        self._proxy_auth = default_proxy_auth
        self._session:aiohttp.ClientSession = aiohttp.ClientSession()

    @staticmethod
    def is_scratch(url:str) -> bool:
        hostname = urlparse(url).hostname
        if hostname is None:
            return False
        return hostname.endswith("scratch.mit.edu")
    
    @property
    def proxy(self) -> tuple[str|None,aiohttp.BasicAuth|None]:
        return self._proxy,self._proxy_auth
    
    def set_proxy(self,url:str|None=None,auth:aiohttp.BasicAuth|None=None):
        self._proxy = url
        self._proxy_auth = auth
    
    def get_cookie(self,url:str) -> dict[str, str]:
        return self.scratch_cookies if self.is_scratch(url) else self.cookies
    
    def _check(self,response:Response):
        url = response._response.url
        status_code = response.status_code
        if url.host == "scratch.mit.edu":
            if url.path.startswith("/ip_ban_appeal/"):
                raise error.IPBanned(response,common.split(url.path,"/ip_ban_appeal/","/"))
            elif url.path.startswith("/accounts/banned-response"):
                raise error.AccountBlocked(response)
            elif url.path.startswith("/accounts/login"):
                raise error.Unauthorized(response)
        if status_code == 401:
            raise error.Unauthorized(response)
        elif status_code == 403:
            raise error.Forbidden(response)
        elif status_code == 404:
            raise error.NotFound(response)
        elif status_code == 429:
            raise error.TooManyRequests(response)
        elif status_code // 100 == 4:
            raise error.ClientError(response)
        elif status_code // 100 == 5:
            raise error.ServerError(response)
    
    async def _request(self,method:str,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        kwargs["cookies"] = kwargs.get("cookies") or self.get_cookie(url)
        kwargs["headers"] = kwargs.get("headers") or self.headers
        check = kwargs.pop("check",True)
        if self.closed:
            raise error.SessionClosed()
        try:
            async with self._session.request(method,url,proxy=self._proxy,proxy_auth=self._proxy_auth,**kwargs) as _response:
                await _response.read()
            response = Response(_response)
        except Exception as e:
            raise error.ProcessingError(e) from e
        if check:
            self._check(response)
        return response

    async def get(self,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        return await self._request("GET",url,**kwargs)
    
    async def post(self,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        return await self._request("POST",url,**kwargs)
    
    async def put(self,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        return await self._request("PUT",url,**kwargs)
    
    async def delete(self,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        return await self._request("DELETE",url,**kwargs)
    
    @property
    def closed(self):
        return self._session.closed
    
    async def close(self):
        await self._session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()