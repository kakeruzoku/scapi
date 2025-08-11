from typing import TYPE_CHECKING, Literal,Any
from ..others import client,error

if TYPE_CHECKING:
    from . import session


class _BaseSiteAPI:
    update_type:Literal["GET","POST","PUT","DELETE",None]=None
    update_url:str|None=None

    def __init__(
            self,
            client_or_session:"client.HTTPClient|session.Session",
        ) -> None:
        if isinstance(client_or_session,client.HTTPClient):
            self.client = client_or_session
            self.session = None
        else:
            self.client = client_or_session.client
            self.session = client_or_session

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