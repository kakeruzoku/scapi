import datetime
from typing import Final
from ..utils import client, common, error, file
from . import base,session,user,project,studio

class Comment(base._BaseSiteAPI):
    def __init__(
            self,
            id:int,
            client_or_session:"client.HTTPClient|session.Session|None"=None,*,
            place:"project.Project|studio.Studio|user.User"
        ):

        super().__init__(client_or_session)
        self.id:Final[int] = id
        self.place = place

        self.parent_id:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.commentee_id:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.content:common.MAYBE_UNKNOWN[str] = common.UNKNOWN

        self._created_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.author:"common.MAYBE_UNKNOWN[user.User]" = common.UNKNOWN
        self.reply_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN

    @property
    def created_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        return common.dt_from_isoformat(self._created_at)