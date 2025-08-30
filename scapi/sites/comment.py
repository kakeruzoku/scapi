import datetime
import json
from typing import AsyncGenerator, Final

import bs4
from ..utils import client, common, error, file
from . import base,session,user,project,studio
from ..utils.types import (
    CommentPayload,
    CommentFailurePayload,
    CommentPostPayload
)

class Comment(base._BaseSiteAPI[int]):
    """
    コメントを表す。

    .. note::
        プロジェクト欄でコメントに関するAPIを使用する場合、プロジェクトの作者のユーザー名が必要です。データが取得されていない可能性がある場合、古いAPIを使用することを検討してください。

    .. note::
        プロフィール欄でコメントに関するAPIを使用する場合、必ず古いAPIが使用されます。新しいAPIでしか利用できない関数では TypeError が送出されることがあります。

    Attributes:
        id (int): コメントID
        place (common.MAYBE_UNKNOWN[Project|Studio|User]): コメントの場所
        parent_id (common.MAYBE_UNKNOWN[int|None]): 親コメントID
        commentee_id (common.MAYBE_UNKNOWN[int|None]): メンションしたユーザーのID
        content (common.MAYBE_UNKNOWN[str]): コメントの内容
        author (common.MAYBE_UNKNOWN[User]): コメントしたユーザー
        reply_count (common.MAYBE_UNKNOWN[int]): コメントにある返信の数
    """
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
    def _root_old_url(place:"project.Project|studio.Studio|user.User"):
        if isinstance(place,project.Project):
            return f"https://scratch.mit.edu/site-api/comments/project/{place.id}/"
        elif isinstance(place,studio.Studio):
            return f"https://scratch.mit.edu/site-api/comments/gallery/{place.id}/"
        elif isinstance(place,user.User):
            return f"https://scratch.mit.edu/site-api/comments/user/{place.username}/"
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

    def _update_from_html(self,data:bs4.element.Tag):
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
        """
        コメントが作成された時間を返す

        Returns:
            datetime.datetime|UNKNOWN_TYPE: データがある場合、その時間。
        """
        return common.dt_from_isoformat(self._created_at)
    
    @property
    def modified_at(self) -> datetime.datetime|common.UNKNOWN_TYPE:
        """
        コメントが最後に編集された時間を返す
        ユーザーがコメントを編集することはできないため、基本的に created_at と同じになります。

        Returns:
            datetime.datetime|UNKNOWN_TYPE: データがある場合、その時間。
        """
        return common.dt_from_isoformat(self._modified_at)
    

    async def get_replies(self,limit:int|None=None,offset:int|None=None,*,use_cache:bool=True) -> AsyncGenerator["Comment", None]:
        """
        コメントの返信を取得する。
        ユーザーページや、作者の不明なプロジェクト欄では取得できません。

        Args:
            limit (int|None, optional): 取得するコメントの数。初期値は40です。
            offset (int|None, optional): 取得するコメントの開始位置。初期値は0です。
            use_cache (bool, optional): 古いAPIから取得した時のキャッシュを使用するか。

        Yields:
            Comment: 取得したコメント
        """
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
        """
        親コメントを取得する。

        Args:
            use_cache (bool, optional): キャッシュを使用するか。デフォルトはTrueです。

        Returns:
            Comment|None|common.UNKNOWN_TYPE: 取得できる場合、取得されたコメント
        """
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
            url = cls._root_old_url(place) + "add/"
        else:
            if isinstance(place,project.Project):
                url =  f"https://api.scratch.mit.edu/proxy/comments/project/{place.id}/"
            elif isinstance(place,studio.Studio):
                url =  f"https://api.scratch.mit.edu/proxy/comments/studio/{place.id}/"
            else:
                raise TypeError("User comment updates are not supported.")
        parent_id = parent.id if isinstance(parent,Comment) else parent
        commentee_id = commentee.id if isinstance(commentee,user.User) else commentee
        if commentee_id is common.UNKNOWN:
            raise error.NoDataError(commentee) # type: ignore

        _data:CommentPostPayload = {
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
                raise error.CommentFailure._from_old_data(response,place._session,_data["content"],error_data)
            soup = bs4.BeautifulSoup(response.text, "html.parser")
            tag = soup.find("div")
            
            comment = Comment._create_from_data(
                int(tag["data-comment-id"]), # type: ignore
                tag,place.client_or_session,
                "_update_from_html",
                place=place,
                _reply=[]
            )
        else:
            data:CommentFailurePayload|CommentPayload = response.json()
            if "rejected" in data:
                raise error.CommentFailure._from_data(response,place._session,_data["content"],data)
            comment = Comment._create_from_data(data["id"],data,place.client_or_session)
        return comment
    
    async def post_reply(
            self,
            content:str,
            commentee:"user.User|int|None|common.UNKNOWN_TYPE"=common.UNKNOWN,
            is_old:bool=False
        ) -> "Comment":
        """
        コメントを返信する。

        Args:
            content (str): コメントの内容
            commentee (User|int|None, optional): メンションする場合、ユーザーかそのユーザーのID
            is_old (bool, optional): 古いAPIを使用して送信するか

        Returns:
            comment.Comment: 投稿されたコメント
        """
        if commentee is common.UNKNOWN:
            commentee = self.author and self.author.id or None
        return await Comment.post_comment(self.place,content,self.parent_id or self.id,commentee,is_old)
    
    async def delete(self,is_old:bool=False):
        """
        コメントを削除する。

        Args:
            is_old (bool, optional): 古いAPIを使用するか
        """
        self.require_session()
        if isinstance(self.place,user.User):
            is_old = True
        if is_old:
            url = self.root_old_url + "del/"
            await self.client.post(url,json={"id":str(self.id)})
        else:
            if isinstance(self.place,project.Project):
                url =  f"https://api.scratch.mit.edu/proxy/comments/project/{self.place.id}/comment/{self.id}"
            elif isinstance(self.place,studio.Studio):
                url =  f"https://api.scratch.mit.edu/proxy/comments/studio/{self.place.id}/comment/{self.id}"
            else:
                raise TypeError("User comment updates are not supported.")
            await self.client.delete(url,json={"reportId":None})

    async def report(self,is_old:bool=False):
        """
        コメントを報告する。

        Args:
            is_old (bool, optional): 古いAPIを使用するか
        """
        self.require_session()
        if isinstance(self.place,user.User):
            is_old = True
        if is_old:
            url = self.root_old_url + "rep/"
            await self.client.post(url,json={"id":str(self.id)})
        else:
            if isinstance(self.place,project.Project):
                url = f"https://api.scratch.mit.edu/proxy/project/{self.place.id}/comment/{self.id}/report"
            elif isinstance(self.place,studio.Studio):
                url = f"https://api.scratch.mit.edu/proxy/studio/{self.place.id}/comment/{self.id}/report"
            else:
                raise TypeError("User comment updates are not supported.")
            await self.client.post(url,json={"reportId":None})

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