from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Self, TypeVar, Generic, ParamSpec, Coroutine
from abc import ABC,abstractmethod
from ..utils.client import HTTPClient
from ..utils.common import UNKNOWN,_bypass_checking,get_client_and_session,temporary_httpclient
from ..utils.error import NoSession
if TYPE_CHECKING:
    from .session import Session

_T = TypeVar("_T")
_P = TypeVar("_P")

class _BaseSiteAPI(ABC,Generic[_T]):
    """
    Scratchの何かしらのオブジェクトを表す。

    Attributes:
        client (HTTPClient): 通信に使用するHTTPクライアント。
        session (Session|None): ログインしている場合、そのセッション。
    """
    @abstractmethod
    def __init__(
            self,
            client_or_session:"HTTPClient|Session|None",
        ) -> None:
        self.client,self.session = get_client_and_session(client_or_session)

    @property
    def client_or_session(self) -> "HTTPClient|Session":
        """
        紐づけられているSessionかHTTPClientを返す。

        Returns:
            HTTPClient|Session
        """
        return self.session or self.client

    async def update(self) -> None:
        """
        APIからデータを更新する。

        Raises:
            TypeError: このクラスでupdate()が定義されていない。
        """
        raise TypeError()
    
    def _update_from_data(self,data):
        return
    
    def _update_to_attributes(self,**data:Any):
        for k,v in data.items():
            if v is UNKNOWN:
                continue
            setattr(self,k,v)

    @property
    def _session(self):
        if self.session is None:
            raise NoSession(self)
        return self.session
    
    @_bypass_checking
    def require_session(self):
        """
        クラスにセッションが紐づけられていない場合、例外を送出する。

        Raises:
            NoSession: セッションが紐づけられていない。
        """
        if self.session is None:
            raise NoSession(self)
    
    @property
    def client_closed(self) -> bool:
        """
        HTTPClientが閉じられているか。

        Returns:
            bool: 接続が閉じられているか
        """
        return self.client.closed
    
    async def client_close(self):
        """
        紐づけられているHTTPClientを閉じる。
        """
        await self.client.close()

    @classmethod
    async def _create_from_api(
        cls,
        id:_T,
        client_or_session:"HTTPClient|Session|None"=None,
        **kwargs
    ):
        async with temporary_httpclient(client_or_session) as client:
            _cls = cls(id,client_or_session or client,**kwargs) # type: ignore
            await _cls.update()
        return _cls
    
    @classmethod
    def _create_from_data(
        cls,
        id:_T,
        data:_P,
        client_or_session:"HTTPClient|Session|None"=None,
        _update_func:Callable[[Self,_P],None]|None=None,
        **kwargs
    ):
        _cls = cls(id,client_or_session,**kwargs) # type: ignore
        if _update_func is None:
            _cls._update_from_data(data)
        else:
            _update_func(_cls,data)
        return _cls

    
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client_close()