import datetime
import random
from typing import AsyncGenerator, Literal, TypedDict, TYPE_CHECKING, overload
import warnings
import json
import bs4

from ..others import  common
from ..others import error as exception
from . import base

if TYPE_CHECKING:
    from . import session,user,studio,project


class Comment(base._BaseSiteAPI):
    id_name = "id"

    def __init__(
            self,
            ClientSession:common.ClientSession,
            id:int,
            place:"project.Project|studio.Studio|user.User",
            scratch_session:"session.Session|None"=None,
            **entries
        ):
        from . import session,user,studio,project

        self.id = id
        self.place:"project.Project|studio.Studio|user.User" = place
        self.type:Literal["Project","Studio","User"]
        if isinstance(self.place,project.Project):
            self.type = "Project"
        elif isinstance(self.place,studio.Studio):
            self.type = "Studio"
        elif isinstance(self.place,user.User):
            self.type = "User"
        else:
            raise TypeError()
        
        super().__init__("get","",ClientSession,scratch_session)

        self.parent_id:int|None = None
        self.commentee_id:int|None = None
        self.content:str = None
        self._sent:str = None
        self.sent:datetime.datetime = None
        self.author:"user.User" = None
        self.reply_count:int = None

        self._parent_cache:"Comment|None" = None
        self._reply_cache:"list[Comment]|None" = None

    @property
    @common.deprecated("Comment","sent_dt","sent")
    def sent_dt(self) -> datetime.datetime:
        return self.sent

    async def _update_comment_old_api(self):
        r = await self.place.get_comment_by_id(self.id,True)
        self.parent_id = r.parent_id
        self.commentee_id = r.commentee_id
        self.content = r.content
        self.sent = r.sent
        self.author = r.author
        self.reply_count = r.reply_count
        self._parent_cache = r._parent_cache
        self._reply_cache = r._reply_cache
        
    async def update(self,is_old:bool|None=None) -> bool: #is_old
        # bool→指定 None→できるだけNew
        if self.type == "Project": #3.0は作者情報が必須
            author_username:str|None = self.place.author and self.place.author.username
            if is_old is None:
                is_old = author_username is None

            if is_old:
                await self._update_comment_old_api()
                return True
            else:
                if author_username is None: raise exception.NoDataError()
                self.update_url = f"https://api.scratch.mit.edu/users/{author_username}/projects/{self.place.id}/comments/{self.id}"
                await super().update()
        elif self.type == "Studio": #基本3.0
            if is_old == True:
                await self._update_comment_old_api()
                return True
            else:
                self.update_url = f"https://api.scratch.mit.edu/studios/{self.place.id}/comments/{self.id}"
                await super().update()
        elif self.type == "User": #2.0APIのみ
            if is_old == False: raise ValueError()
            await self._update_comment_old_api()
            return True
        else:
            raise TypeError()
        return False
    
    def _update_from_dict(self, data:dict) -> None:
        from .user import User
        self.parent_id = data.get("parent_id",self.parent_id)
        self.commentee_id = data.get("commentee_id",self.commentee_id)
        self.content = data.get("content",self.content)
        self._add_datetime("sent",data.get("datetime_created"))
        _author:dict = data.get("author",{})
        self.author = User(self.ClientSession,_author.get("username"),self.Session)
        self.author._update_from_dict(_author)
        self.reply_count = data.get("reply_count",self.reply_count)

        #User Comment Only
        self._reply_cache = data.get("_reply_cache",self._reply_cache)
        self._parent_cache = data.get("_parent_cache",self._parent_cache)

    async def reply(self, content, *, commentee:"user.User|int|None"=None,is_old:bool|None=None):
        if is_old is None:
            is_old = self.type == "User"
        return await self.place.post_comment(content,self,commentee,is_old)

    async def get_replies(self, *, limit=40, offset=0):
        if self.type == "Project":
            if ((self.place.author and self.place.author.username) is None):
                return self._get_replies(limit,offset)
            return base.get_object_iterator(
                self.ClientSession,
                f"https://api.scratch.mit.edu/users/{self.place.author.username}/projects/{self.place.id}/comments/{self.id}/replies/",
                None,Comment,limit=limit,offset=offset,add_params={"cachebust":random.randint(0,9999)},
                custom_func=base._comment_iterator_func, others={"plece":self}
            )
        elif self.type == "User":
            return self._get_replies(limit,offset)
        elif self.type == "Studio":
            return base.get_object_iterator(
                self.ClientSession,
                f"https://api.scratch.mit.edu/studios/{self.place.id}/comments/{self.id}/replies/",
                None,Comment,limit=limit,offset=offset,add_params={"cachebust":random.randint(0,9999)},
                custom_func=base._comment_iterator_func, others={"plece":self}
            )


    async def _get_replies(self, limit:int, offset:int) -> AsyncGenerator["Comment",None]:
        common.no_data_checker(self._reply_cache)
        for c in self._reply_cache[offset:limit+offset]:
            yield c

    async def delete(self,is_old:bool|None) -> bool:
        self.has_session_raise()
        if is_old is None:
            is_old = self.type == "User"
        if is_old:
            data = {"id":str(self.id)}
            if self.type == "Project":
                url = f"https://scratch.mit.edu/site-api/comments/project/{self.place.id}/del/"
            elif self.type == "Studio":
                url = f"https://scratch.mit.edu/site-api/comments/gallery/{self.place.id}/del/"
            elif self.type == "User":
                url = f"https://scratch.mit.edu/site-api/comments/user/{self.place.username}/del/"
            else:
                raise ValueError()
            r = await self.ClientSession.post(url,json=data)
        else:
            data = {"reportId":None}
            if self.type == "Project":
                url = f"https://api.scratch.mit.edu/proxy/comments/project/{self.place.id}/comment/{self.id}"
            elif self.type == "Studio":
                url = f"https://api.scratch.mit.edu/proxy/comments/studio/{self.place.id}/comment/{self.id}"
            else:
                raise ValueError()
            r = await self.ClientSession.delete(url,json=data)
        
        return r.status_code == 200
    
    async def report(self,is_old:bool|None):
        self.has_session_raise()
        if is_old is None:
            is_old = self.type == "User"
        if is_old:
            data = {"id":str(self.id)}
            if self.type == "Project":
                url = f"https://scratch.mit.edu/site-api/comments/project/{self.place.id}/rep/"
            elif self.type == "Studio":
                url = f"https://scratch.mit.edu/site-api/comments/gallery/{self.place.id}/rep/"
            elif self.type == "User":
                url = f"https://scratch.mit.edu/site-api/comments/user/{self.place.username}/rep/"
            else:
                raise ValueError()
        else:
            data = {"reportId":None}
            if self.type == "Project":
                url = f"https://api.scratch.mit.edu/proxy/project/{self.place.id}/comment/{self.id}/report"
            elif self.type == "Studio":
                url = f"https://api.scratch.mit.edu/proxy/studio/{self.place.id}/comment/{self.id}/report"
            else:
                raise ValueError()
        r = await self.ClientSession.post(url,json=data)
        return r.status_code == 200
        

        
    
async def _post_comment(
        obj:"project.Project|studio.Studio|user.User",
        url:str,
        is_old:bool,
        content:str,
        commentee_id:int,
        parent_id:int
    ) -> Comment:
    obj.has_session_raise()
    header = obj.ClientSession._header if is_old else obj.ClientSession._header|{"referer":obj.url}
    text = (await obj.ClientSession.post(url,json={
        "commentee_id": commentee_id or "",
        "content": str(content),
        "parent_id": parent_id or "",
    },header=header)).text
    if is_old:
        if text.strip().startswith('<script id="error-data" type="application/json">'):#エラー
            data:dict = json.loads(common.split(text,'type="application/json">',"</script>"))
            raise exception.CommentFailure(data.get("error"))
    
        c = Comment(obj.ClientSession,common.split_int(text,"data-comment-id=\"","\">"),obj,obj.Session)

        c._update_from_dict({
            "parent_id":parent_id,
            "commentee_id":commentee_id,
            "datetime_create":common.split(text,"<span class=\"time\" title=\"","\">"),
            "content":content,
            "author":{
                "username":common.split(text,"data-comment-user=\"","\">"),
                "id":common.split_int(text,"src=\"//cdn2.scratch.mit.edu/get_image/user/","_")
            },
            "reply_count":0,"page":1,"_reply_cache":[]
        })

        if c.id is None:
            raise exception.NoPermission()
    else:
        resp = json.loads(text)
        if "rejected" in resp:
            raise exception.CommentFailure(resp["rejected"])
        
        c = Comment(obj.ClientSession,resp["id"],obj,obj.Session)
        c._update_from_dict(resp)
    return c

async def _get_comment_old_api_by_id(
        obj:"project.Project|studio.Studio|user.User",url:str,id:int
    ):
    id = int(id)
    async for i in _get_comments_old_api(obj,url,start_page=1,end_page=67):
        if id == i.id:
            return i
        for r in i._reply_cache or []:
            if id == r.id:
                return r
    raise exception.ObjectNotFound(Comment,ValueError)

async def _get_comments_old_api(
        obj:"project.Project|studio.Studio|user.User",url:str, *, start_page:int=1, end_page:int=1
    ) -> AsyncGenerator[Comment, None]:
    if end_page > 67:
        end_page = 67
    for i in range(start_page,end_page+1):
        r = await obj.ClientSession.get(url,check=False,params={"page":i})
        if r.status_code == 404: return
        if r.status_code == 503: raise exception.ObjectNotFound(obj.__class__,exception.ServerError(r))
        soup = bs4.BeautifulSoup(r.text, "html.parser")
        _comments:bs4.element.ResultSet[bs4.element.Tag] = soup.find_all("li", {"class": "top-level-reply"})

        for _comment in _comments:
            id = int(_comment.find("div", {"class": "comment"})['data-comment-id'])
            username:str = _comment.find("a", {"id": "comment-user"})['data-comment-user']
            userid = int(_comment.find("a",{"class":"reply"})["data-commentee-id"])

            content = str(_comment.find("div", {"class": "content"}).text).strip()
            send_dt = _comment.find("span", {"class": "time"})['title']

            main = Comment(obj.ClientSession,id,obj,obj.Session)
            replies:bs4.element.ResultSet[bs4.element.Tag] = _comment.find_all("li", {"class": "reply"})
            replies_obj:list[Comment] = []
            for reply in replies:
                r_id = int(reply.find("div", {"class": "comment"})['data-comment-id'])
                r_username:str = reply.find("a", {"id": "comment-user"})['data-comment-user']

                r_userid = int(reply.find("a",{"class":"reply"})["data-commentee-id"])
                r_content = str(reply.find("div", {"class": "content"}).text).strip()
                r_send_dt = reply.find("span", {"class": "time"})['title']
                reply_obj = Comment(obj.ClientSession,id,obj,obj.Session)
                reply_obj._update_from_dict({
                    "id":r_id,"parent_id":id,"commentee_id":None,"content":r_content,"datetime_created":r_send_dt,"author":{"username":r_username,"id":r_userid},"_parent_cache":main,"reply_count":0
                })
                replies_obj.append(reply_obj)

            main._update_from_dict({
                "id":id,"parent_id":None,"commentee_id":None,"content":content,"datetime_created":send_dt,
                "author":{"username":username,"id":userid},
                "_reply_cache":replies_obj,"reply_count":len(replies_obj)
            })
            yield main



def create_Partial_Comment(comment_id:int,place:"project.Project|studio.Studio|user.User",content:str|None=None,author:"user.User|None"=None,*,ClientSession:common.ClientSession|None=None,session:"session.Session|None"=None) -> Comment:
    ClientSession = common.create_ClientSession(ClientSession,session)
    _comment = Comment(ClientSession,comment_id,place,session)
    _comment.id = comment_id
    _comment.author = author or _comment.author
    _comment.content = content or _comment.content
    return _comment
