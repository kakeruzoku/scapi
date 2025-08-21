import datetime
import json
from typing import AsyncGenerator, Final

import bs4
from ..utils import client, common, error, file
from . import base,session,user,project,studio
from ..utils.types import (
    CommentPayload,
    CommentFailurePayload
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
            _parent:"Comment|None|common.UNKNOWN_TYPE" = common.UNKNOWN,
            _reply:"list[Comment]|None" = None
        ):

        super().__init__(place.client_or_session)
        self.id:Final[int] = id
        self.place = place

        self.parent_id:common.MAYBE_UNKNOWN[int|None] = _parent.id if isinstance(_parent,Comment) else _parent
        self.commentee_id:common.MAYBE_UNKNOWN[int|None] = common.UNKNOWN
        self.content:common.MAYBE_UNKNOWN[str] = common.UNKNOWN

        self._created_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self._modified_at:common.MAYBE_UNKNOWN[str] = common.UNKNOWN
        self.author:"common.MAYBE_UNKNOWN[user.User]" = common.UNKNOWN
        self.reply_count:common.MAYBE_UNKNOWN[int] = common.UNKNOWN

        self._cached_parent:"Comment|None" = _parent or None
        self._cached_reply:"list[Comment]|None" = _reply

    @staticmethod
    def _root_url(place:"project.Project|studio.Studio|user.User"):
        if isinstance(place,project.Project):
            return f"https://api.scratch.mit.edu/users/{place._author_username}/projects/{place.id}/comments/"
        elif isinstance(place,studio.Studio):
            return f"https://api.scratch.mit.edu/studios/{place.id}/comments/"
        else:
            raise TypeError("User comment updates are not supported.")


    @property
    def root_url(self):
        return self._root_url(self.place) + str(self.id)
    
    @staticmethod
    def _root_proxy_url(place:"project.Project|studio.Studio|user.User"):
        if isinstance(place,project.Project):
            return f"https://api.scratch.mit.edu/proxy/project/{place.id}/comment/"
        elif isinstance(place,studio.Studio):
            return f"https://api.scratch.mit.edu/proxy/studio/{place.id}/comment/"
        else:
            raise TypeError("User comment updates are not supported.")

    @property
    def root_proxy_url(self):
        return self._root_proxy_url(self.place) + str(self.id)
        
    @staticmethod
    def _root_old_url(place:"project.Project|studio.Studio|user.User"):
        if isinstance(place,project.Project):
            return f"https://scratch.mit.edu/site-api/comments/project/{place.id}"
        elif isinstance(place,studio.Studio):
            return f"https://scratch.mit.edu/site-api/comments/gallery/{place.id}"
        elif isinstance(place,user.User):
            return f"https://scratch.mit.edu/site-api/comments/user/{place.username}"
        else:
            raise TypeError("Unknown comment place type.")

    @property
    def root_old_url(self):
        return self._root_old_url(self.place)

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
        if use_cache and self._cached_reply is not None:
            if limit is None:
                limit = 40
            if offset is None:
                offset = 0
            for c in self._cached_reply[offset:offset+limit]:
                yield c
        else:
            url = self.root_url + "/replies"
            async for _c in common.api_iterative(self.client,url,limit,offset):
                yield Comment._create_from_data(_c["id"],_c,place=self.place)

    async def get_parent(self,use_cache:bool=True) -> "Comment|None|common.UNKNOWN_TYPE":
        if not isinstance(self.parent_id,int):
            return self.parent_id
        if self._cached_parent is None or use_cache:
            self._cached_parent = await Comment._create_from_api(self.parent_id,place=self.place)
        return self._cached_parent
    
    
    @classmethod
    async def post_comment(
        cls,place:"project.Project|studio.Studio|user.User",
        content:str,parent:"Comment|int|None",commentee:"user.User|int|None",
        is_old:bool=False
    ) -> "Comment":
        place.require_session()

        if isinstance(place,user.User):
            is_old = True
        if is_old:
            url = cls._root_old_url(place)
        else:
            url = cls._root_proxy_url(place)
        parent_id = parent.id if isinstance(parent,Comment) else parent
        commentee_id = commentee.id if isinstance(commentee,user.User) else commentee
        if commentee_id is common.UNKNOWN:
            raise error.NoDataError(commentee) # type: ignore

        _data = {
            "commentee_id": commentee_id or "",
            "content": str(content),
            "parent_id": parent_id or "",
        }

        response = await place.client.post(url,json=_data)

        if is_old:
            text = response.text.strip()
            if text.startswith('<script id="error-data" type="application/json">'):
                error_data = json.loads(common.split(
                    text,'<script id="error-data" type="application/json">',"</script>",True
                ))
                raise error.CommentFailure.from_old_data(response,place._session,error_data)
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            comment = Comment._create_from_data(
                int(soup["data-comment-id"]), # type: ignore
                soup,place.client_or_session,
                "_update_from_html",
                place=place,
                _reply=[]
            )
        else:
            data:CommentFailurePayload|CommentPayload = response.json()
            if "rejected" in data:
                raise error.CommentFailure.from_data(response,place._session,data)
            comment = Comment._create_from_data(data["id"],data,place.client_or_session)
        return comment

async def get_comment_from_old(
        place:"project.Project|studio.Studio|user.User",
        start_page:int|None=None,end_page:int|None=None
    ) -> AsyncGenerator[Comment,None]:
    if start_page is None:
        start_page = 1
    if end_page is None:
        end_page = start_page

    url = Comment._root_old_url(place)

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
                _parent=None,
                _reply=[]
            )
            assert c._cached_reply is not None
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