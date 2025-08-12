from typing import TYPE_CHECKING, Literal,Any,TypeVar, Generic
from abc import ABC,abstractmethod
from ..others import client,error

if TYPE_CHECKING:
    from . import session

_T_ID = TypeVar("_T_ID")

class _BaseSiteAPI(ABC,Generic[_T_ID]):

    @abstractmethod
    def __init__(
            self,
            client_or_session:"client.HTTPClient|session.Session|None",
        ) -> None:
        if client_or_session is None:
            client_or_session = client.HTTPClient()
        if isinstance(client_or_session,client.HTTPClient):
            self.client = client_or_session
            self.session = None
        else:
            self.client = client_or_session.client
            self.session = client_or_session

    async def update(self) -> None:
        raise TypeError()
    
    def _update_from_data(self,data):
        return
    
    def _update_to_attributes(self,data:dict[str,Any]):
        for k,v in data.items():
            if v is None:
                return
            setattr(self,k,v)

    @property
    def has_session(self) -> bool:
        return self.session is not None

    def require_session(self):
        if not self.has_session:
            raise error.NoSession()
    
    @property
    def client_closed(self) -> bool:
        return self.client.closed
    
    async def client_close(self):
        await self.client.close()

    @classmethod
    async def _create_from_api(
        cls,
        id:_T_ID,
        client_or_session:"client.HTTPClient|session.Session|None"=None,
        **others
    ):
        _cls = cls(id,client_or_session,**others) # type: ignore
        await _cls.update()
        return _cls
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client_close()