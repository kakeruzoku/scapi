import datetime
from typing import AsyncGenerator, Final

import bs4
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
            _parent:"Comment|None" = None,
            _reply:"list[Comment]|common.UNKNOWN_TYPE" = common.UNKNOWN
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

        self._cached_parent:"Comment|None" = _parent
        self._cached_reply:common.MAYBE_UNKNOWN["list[Comment]"] = _reply

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

    def _update_from_html(self,data:bs4.BeautifulSoup|bs4.element.Tag):
        comment = data

        _created_at = str(comment.find("span", class_="time")["title"]) # type: ignore
        self._update_to_attributes(
            content=str(comment.find("div", class_="content").get_text(strip=True)), # type: ignore
            _created_at=_created_at,
            _modified_at=_created_at,
        )
        author_username = comment.find("div", class_="name").get_text(strip=True) # type: ignore
        author_user_id = int(comment.find("a", class_="reply")["data-commentee-id"]) # type: ignore
        if self.author is common.UNKNOWN:
            self.author = user.User(author_username,self.client_or_session)
        self.author.id = author_user_id

    @property
    def created_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        return common.dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        return common.dt_from_isoformat(self._modified_at)
    

    async def get_reply(self,limit:int|None=None,offset:int|None=None,*,use_cache:bool=True) -> AsyncGenerator["Comment", None]:
        if use_cache and self._cached_reply is not common.UNKNOWN:
            limit = limit or 40
            offset = offset or 0
            for c in self._cached_reply[offset:offset+limit]:
                yield c
        url = self.root_url + "/replies"
        async for _c in common.api_iterative(self.client,url,limit,offset):
            yield Comment._create_from_data(_c["id"],_c,place=self.place)

async def get_comment_from_old(
        place:"project.Project|studio.Studio|user.User",
        start_page:int|None=None,end_page:int|None=None
    ) -> AsyncGenerator[Comment,None]:
    if start_page is None:
        start_page = 1
    if end_page is None:
        end_page = start_page

    if isinstance(place,project.Project):
        url = f"https://scratch.mit.edu/site-api/comments/project/{place.id}"
    elif isinstance(place,studio.Studio):
        url = f"https://scratch.mit.edu/site-api/comments/gallery/{place.id}"
    elif isinstance(place,user.User):
        url = f"https://scratch.mit.edu/site-api/comments/user/{place.username}"
    else:
        raise TypeError("Unknown comment place type.")

    for i in range(start_page,end_page+1):
        try:
            response = await place.client.get(url,params={"page":i})
        except error.NotFound:
            return
        except error.ServerError as e:
            raise error.NotFound(e.response)
        
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        _comments = soup.find_all("li", {"class": "top-level-reply"})
        for _comment_outside in _comments:
            _comment = _comment_outside.find("div") # type: ignore
            c = Comment._create_from_data(
                int(_comment["data-comment-id"]), # type: ignore
                _comment,
                place.client_or_session,
                "_update_from_html",
                place=place,
                _reply=[]
            )
            assert c._cached_reply is not common.UNKNOWN
            _comment_replies = _comment_outside.find("ul", {"class":"replies"}) # type: ignore
            _replies = _comment_replies.find_all("div", {"class": "comment"}) # type: ignore
            for _reply in _replies:
                c._cached_reply.append(Comment._create_from_data(
                    int(_reply["data-comment-id"]), # type: ignore
                    _reply,
                    place.client_or_session,
                    "_update_from_html",
                    place=place,
                    _parent=c,
                    _reply=[]
                ))
            yield c