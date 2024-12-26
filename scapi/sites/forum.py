import datetime
import random
from typing import AsyncGenerator, Literal, TypedDict, TYPE_CHECKING, overload
import warnings

from ..others import  common
from ..others import error as exception
from . import base

if TYPE_CHECKING:
    from .session import Session
    from .user import User

class ForumTopic(base._BaseSiteAPI):
    raise_class = exception.ForumTopicNotFound
    id_name = "id"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        id:int,
        scratch_session:"Session|None"=None,
        **entries
    ):
        super().__init__("get",f"https://scratch.mit.edu/discuss/feeds/topic/{id}/",ClientSession,scratch_session)

        self._session = None
        self.id:int = None
        self.reply_count:int|None = None
        self.view_count:int|None = None
        self.category_name:str = None
        self.last_updated:str|None = None

    def _update_from_dict(self, data):
        pass

def create_Partial_ForumTopic(Topic_id:int|None=None,*,ClientSession:common.ClientSession|None=None,session:"Session|None"=None) -> ForumTopic:
    ClientSession = common.create_ClientSession(ClientSession)
    return ForumTopic(ClientSession,Topic_id,session)
