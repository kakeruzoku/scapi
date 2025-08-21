import datetime
from typing import Final
from ..utils import client, common, error, file
from . import base,session,user,project,studio
from ..utils.types import (
    CommentPayload
)

class Comment(base._BaseSiteAPI[int]):
    def __init__(
            self,
            id:int,
            client_or_session:"client.HTTPClient|session.Session|None"=None,
            *,place:"project.Project|studio.Studio|user.User"
        ):

        super().__init__(place.client_or_session)
        self.id:Final[int] = id
        self.place = place

        self.parent_id:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.commentee_id:common.MAYBE_UNKNOWN[int] = common.UNKNOWN
        self.content:common.MAYBE_UNKNOWN[str] = common.UNKNOWN

        self._created_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self._modified_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.author:"common.MAYBE_UNKNOWN[user.User]" = common.UNKNOWN
        self.reply_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN

    async def update(self):
        if isinstance(self.place,project.Project):
            url = f"https://api.scratch.mit.edu/users/{self.place._author_username}/projects/{self.place.id}/comments/{self.id}"
        elif isinstance(self.place,studio.Studio):
            url = f"https://api.scratch.mit.edu/studios/{self.place.id}/comments/{self.id}"
        else:
            raise TypeError("User comment updates are not supported.")
        
        response = await self.client.get(url)
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