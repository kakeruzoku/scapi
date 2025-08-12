from typing import TYPE_CHECKING
from ..others import client, common, error
from . import base

if TYPE_CHECKING:
    from . import session

class User(base._BaseSiteAPI[str]):

    def __init__(self,username:str,client_or_session:"client.HTTPClient|session.Session|None"=None):
        super().__init__(client_or_session)
        self.username:str = username
        self.id:int|None = None

        self._joined_at:str|None = None

        self.status:str|None = None
        self.bio:str|None = None
        self.country:str|None = None
        self.scratchteam:bool|None = None

    @property
    def update_url(self):
        return f"https://api.scratch.mit.edu/users/{self.username}"