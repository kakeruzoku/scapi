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
        self.id = id
        self.place = place

        self.parent_id:int|None = None
        self.commentee_id:int|None = None
        self.content:str|None = None

        self._created_at:str|None = None
        self.author:"user.User|None" = None
        self.reply_count:int|None = None

    @property
    def created_at(self):
        return common.dt_from_isoformat(self._created_at)