from typing import TYPE_CHECKING, Literal,Any
from ..others import requests,error

if TYPE_CHECKING:
    from . import session


class _BaseSiteAPI:
    update_type:Literal["GET","POST","PUT","DELETE",None]=None
    update_url:str|None=None

    def __init__(
            self,
            client:requests.HTTPclient,
            session:"session.Session|None"=None,
        ) -> None:
        self.client = client
        self._session:"session.Session|None" = session

    @property
    def has_session(self) -> bool:
        return self._session is not None

    def require_session(self):
        if not self.has_session:
            raise error.NoSession()
    
    @property
    def session_closed(self) -> bool:
        return self.client.closed
    
    async def session_close(self):
        await self.client.close()