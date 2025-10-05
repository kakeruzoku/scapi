from __future__ import annotations

from typing import Any, Callable, TypedDict, Unpack
import aiohttp
import json as _json
from urllib.parse import urlparse
from .config import _config
from .error import (
    SessionClosed,
    ProcessingError,
    IPBanned,
    AccountBlocked,
    Unauthorized,
    Forbidden,
    NotFound,
    TooManyRequests,
    ClientError,
    ServerError,
    RegistrationRequested,
    ResetPasswordRequested
)
from .common import split,UnknownDict

default_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36",
    "x-csrftoken": "a",
    "x-requested-with": "XMLHttpRequest",
    "referer": "https://scratch.mit.edu",
}

class _RequestOptions(TypedDict, total=False):
    params: dict[str,str|int|float]
    data: Any
    json: Any
    cookies: dict[str,str]|None
    headers: dict[str,str]|None
    check: bool

class Response:
    """
    リクエストのレスポンスを表すクラス。

    Attributes:
        client (HTTPClient): 通信に使用したHTTPClient
        _response (aiohttp.ClientResponse):
        status_code (int): HTTPステータスコード
        _body (bytes):
    """
    def __init__(self,response:aiohttp.ClientResponse,client:"HTTPClient"):
        self.client = client
        self._response = response
        self.status_code:int = response.status
        self._body = response._body or b""

    def _check(self):
        url = self._response.url
        status_code = self.status_code
        if url.host == "scratch.mit.edu":
            if url.path.startswith("/ip_ban_appeal/"):
                raise IPBanned(self,split(url.path,"/ip_ban_appeal/","/"))
            elif url.path.startswith("/accounts/banned-response"):
                raise AccountBlocked(self)
            elif url.path.startswith("/accounts/login"):
                raise Unauthorized(self)
            elif url.path.startswith("/classes/complete_registration"):
                raise RegistrationRequested(self)
            elif url.path.startswith("/classes/student_password_reset"):
                raise ResetPasswordRequested(self)
        if status_code == 401:
            raise Unauthorized(self)
        elif status_code == 403:
            raise Forbidden(self)
        elif status_code == 404:
            raise NotFound(self)
        elif status_code == 429:
            raise TooManyRequests(self)
        elif status_code // 100 == 4:
            raise ClientError(self)
        elif status_code // 100 == 5:
            raise ServerError(self)

    @property
    def data(self) -> bytes:
        """
        レスポンスの生データ。

        Returns:
            bytes:
        """
        return self._body
    
    @property
    def text(self) -> str:
        """
        レスポンスのテキスト。

        Returns:
            str:
        """
        return self._body.decode(self._response.get_encoding())
    
    def json(self,loads:Callable[[str], Any]=_json.loads,use_unknown:bool=True,/,**kwargs) -> Any:
        """
        レスポンスをjsonに変換する。

        Args:
            loads (Callable[[str], Any], optional): json.loadsの代わりに使うjsonデコーダー
            use_unknown (bool, optional): .get() を使用した際、キーがないのとnullを区別するためにUNKNOWNを返すdictを使用するか。デフォルトはTrueです。
        """
        if use_unknown:
            kwargs["object_hook"] = UnknownDict
        return loads(self.text,**kwargs)
    
    def json_or_text(self,loads:Callable[[str], Any]=_json.loads,use_unknown:bool=True,/,**kwargs) -> Any:
        """
        jsonをエンコードした結果か、失敗した場合テキストを返す。

        Args:
            loads (Callable[[str], Any], optional): json.loadsの代わりに使うjsonデコーダー
            use_unknown (bool, optional): .get() を使用した際、キーがないのとnullを区別するためにUNKNOWNを返すdictを使用するか。デフォルトはTrueです。
        """
        try:
            return self.json(loads,use_unknown,**kwargs)
        except Exception:
            return self.text

class HTTPClient:
    """
    通信を行うためのClient

    Attributes:
        headers (dict[str,str]):
        cookies (dict[str,str]):
        scratch_headers (dict[str,str]): Scratchドメインにリクエストする場合のヘッダー
        scratch_cookies (dict[str,str]): Scratchドメインにリクエストする場合のクッキー
    """
    def __repr__(self):
        return f"<HTTPClient proxy:{bool(self._proxy)}>"

    def __init__(
            self,*,
            headers:dict[str,str]|None=None,
            cookies:dict[str,str]|None=None,
            scratch_headers:dict[str,str]|None=None,
            scratch_cookies:dict[str,str]|None=None
        ):
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.scratch_headers = scratch_headers or default_headers
        self.scratch_cookies = scratch_cookies or {}
        self._proxy = _config.default_proxy
        self._proxy_auth = _config.default_proxy_auth
        self._session:aiohttp.ClientSession = aiohttp.ClientSession(
            cookie_jar=aiohttp.DummyCookieJar()
        )

    @staticmethod
    def is_scratch(url:str) -> bool:
        """
        urlがscratch.mit.eduドメインを指しているか検証する。

        Args:
            url (str): 検証したいURL

        Returns:
            bool:
        """
        hostname = urlparse(url).hostname
        if hostname is None:
            return False
        return hostname.endswith("scratch.mit.edu")
    
    @property
    def proxy(self) -> tuple[str|None,aiohttp.BasicAuth|None]:
        """
        プロキシの設定を返す。

        Returns:
            tuple[str|None,aiohttp.BasicAuth|None]:
        """
        return self._proxy,self._proxy_auth
    
    def set_proxy(self,url:str|None=None,auth:aiohttp.BasicAuth|None=None):
        """
        プロキシを設定する。

        Args:
            url (str | None, optional): プロキシのURL。Noneでプロキシを使用しません
            auth (aiohttp.BasicAuth | None, optional): プロキシの認証
        """
        self._proxy = url
        self._proxy_auth = auth
    
    async def _request(self,method:str,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        kwargs["cookies"] = kwargs.get("cookies")
        kwargs["headers"] = kwargs.get("headers")

        if kwargs["cookies"] is None: kwargs["cookies"] = self.scratch_cookies if self.is_scratch(url) else self.cookies
        if kwargs["headers"] is None: kwargs["headers"] = self.scratch_headers if self.is_scratch(url) else self.headers
        
        check = kwargs.pop("check",True)
        if self.closed:
            raise SessionClosed()
        try:
            async with self._session.request(method,url,proxy=self._proxy,proxy_auth=self._proxy_auth,**kwargs) as _response:
                await _response.read()
            response = Response(_response,self)
        except Exception as e:
            raise ProcessingError(e) from e
        if check:
            response._check()
        return response

    async def get(self,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        """
        GETリクエストを送信する。

        Args:
            url (str): リクエスト先のURL
            params (dict[str,str|int|float], optional): URLパラメーター
            cookies (dict[str,str]|None, optional): クッキーを上書きする
            headers (dict[str,str]|None, optional): ヘッダーを上書きする
            check (bool, optional): レスポンスコードなどに基づいて例外を送出するか。デフォルトはTrueです。

        Returns:
            Response:
        """
        return await self._request("GET",url,**kwargs)
    
    async def post(self,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        """
        POSTリクエストを送信する。

        Args:
            url (str): リクエスト先のURL
            params (dict[str,str|int|float], optional): URLパラメーター
            data (Any, optional): リクエスト本文
            json (Any, optional): リクエスト本文のjson
            cookies (dict[str,str]|None, optional): クッキーを上書きする
            headers (dict[str,str]|None, optional): ヘッダーを上書きする
            check (bool, optional): レスポンスコードなどに基づいて例外を送出するか。デフォルトはTrueです。

        Returns:
            Response:
        """
        return await self._request("POST",url,**kwargs)
    
    async def put(self,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        """
        PUTリクエストを送信する。

        Args:
            url (str): リクエスト先のURL
            params (dict[str,str|int|float], optional): URLパラメーター
            data (Any, optional): リクエスト本文
            json (Any, optional): リクエスト本文のjson
            cookies (dict[str,str]|None, optional): クッキーを上書きする
            headers (dict[str,str]|None, optional): ヘッダーを上書きする
            check (bool, optional): レスポンスコードなどに基づいて例外を送出するか。デフォルトはTrueです。

        Returns:
            Response:
        """
        return await self._request("PUT",url,**kwargs)
    
    async def delete(self,url:str,**kwargs:Unpack[_RequestOptions]) -> Response:
        """
        DELETEリクエストを送信する。

        Args:
            url (str): リクエスト先のURL
            params (dict[str,str|int|float], optional): URLパラメーター
            data (Any, optional): リクエスト本文
            json (Any, optional): リクエスト本文のjson
            cookies (dict[str,str]|None, optional): クッキーを上書きする
            headers (dict[str,str]|None, optional): ヘッダーを上書きする
            check (bool, optional): レスポンスコードなどに基づいて例外を送出するか。デフォルトはTrueです。

        Returns:
            Response:
        """
        return await self._request("DELETE",url,**kwargs)
    
    @property
    def closed(self):
        """
        クライアントが閉じているか

        Returns:
            bool:
        """
        return self._session.closed
    
    async def close(self):
        """
        クライアントを閉じる
        """
        await self._session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.close()