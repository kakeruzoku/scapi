import datetime
from typing import AsyncGenerator, Final
from ..utils import client, common, error, file
from . import base,session,user,project,studio
from ..utils.types import (
    CommentPayload
)

class Comment(base._BaseSiteAPI[int]):

    def __repr__(self) -> str:
        return f"<Comment id:{self.id} content:{self.content} place:{self.place} user:{self.author} Session:{self.session}>"

    def __init__(
            self,
            id:int,
            client_or_session:"client.HTTPClient|session.Session|None"=None,
            *,
            place:"project.Project|studio.Studio|user.User",
            _parent:"Comment|None" = None
        ):

        super().__init__(place.client_or_session)
        self.id:Final[int] = id
        self.place = place

        self.parent_id:common.MAYBE_UNKNOWN[int] = common.UNKNOWN if _parent is None else _parent.id
        self.commentee_id:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.content:common.MAYBE_UNKNOWN[str] = common.UNKNOWN

        self._created_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self._modified_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.author:"common.MAYBE_UNKNOWN[user.User]" = common.UNKNOWN
        self.reply_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN

        self._cached_parent_comment:"Comment|None" = _parent

    @property
    def root_url(self):
        if isinstance(self.place,project.Project):
            return f"https://api.scratch.mit.edu/users/{self.place._author_username}/projects/{self.place.id}/comments/{self.id}"
        elif isinstance(self.place,studio.Studio):
            return f"https://api.scratch.mit.edu/studios/{self.place.id}/comments/{self.id}"
        else:
            raise TypeError("User comment updates are not supported.")
        
    @property
    def root_proxy_url(self):
        if isinstance(self.place,project.Project):
            return f"https://api.scratch.mit.edu/proxy/project/{self.place.id}/comment/{self.id}"
        elif isinstance(self.place,studio.Studio):
            return f"https://api.scratch.mit.edu/proxy/studio/{self.place.id}/comment/{self.id}"
        else:
            raise TypeError("User comment updates are not supported.")
        
    @property
    def root_old_url(self):
        if isinstance(self.place,project.Project):
            return f"https://scratch.mit.edu/site-api/comments/project/{self.place.id}"
        elif isinstance(self.place,studio.Studio):
            return f"https://scratch.mit.edu/site-api/comments/gallery/{self.place.id}"
        elif isinstance(self.place,user.User):
            return f"https://scratch.mit.edu/site-api/comments/user/{self.place.username}"
        else:
            raise TypeError("Unknown comment place type.")

    async def update(self):
        response = await self.client.get(self.root_url)
        self._update_from_data(response.json())
        
    def _update_from_data(self, data:CommentPayload):
        self._update_to_attributes(
            parent_id=data.get("parent_id"),
            commentee_id=data.get("commentee_id"),
            content=data.get("content"),
            _created_at=data.get("datetime_created"),
            _modified_at=data.get("datetime_modified"),
            reply_count=data.get("reply_count")
        )

        _author = data.get("author")
        if _author:
            if self.author is common.UNKNOWN:
                self.author = user.User(_author.get("username"),self.client_or_session)
            self.author._update_from_data(_author)

    @property
    def created_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        return common.dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        return common.dt_from_isoformat(self._modified_at)
    

    async def get_reply(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Comment", None]:
        url = self.root_url + "/replies"
        async for _c in common.api_iterative(self.client,url,limit,offset):
            yield Comment._create_from_data(_c["id"],_c,place=self.place)