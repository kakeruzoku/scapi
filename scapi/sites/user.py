import datetime
import random
from typing import AsyncGenerator, Generator, Literal, TypedDict, TYPE_CHECKING

from ..others import common
from ..others import error as exception
from . import base,project,comment,activity

import bs4

if TYPE_CHECKING:
    from . import session
    

class User(base._BaseSiteAPI):
    raise_class = exception.UserNotFound
    id_name = "username"

    def __str__(self):
        return f"<User username:{self.username} id:{self.id} Session:{self.Session}>"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        username:str,
        scratch_session:"session.Session|None"=None,
        **entries
    ) -> None:
        super().__init__("get",f"https://api.scratch.mit.edu/users/{username}",ClientSession,scratch_session)

        self.id:int = None
        self.username:str = username

        self._join_date:str = None
        self.join_date:datetime.datetime = None

        self.about_me:str = None
        self.wiwo:str = None
        self.country:str = None
        self.scratchteam:bool = None

        self._website_data:common.Response|None = None

    def _update_from_dict(self, data:dict) -> None:
        self.id = data.get("id",self.id)
        self.username = data.get("username",self.username)
        self.scratchteam = data.get("scratchteam",self.scratchteam)
        self._join_date = data.get("history",{}).get("joined",None)
        self.join_date = common.to_dt(self._join_date,self.join_date)

        _profile:dict = data.get("profile",{})
        self.about_me = _profile.get("bio",self.about_me)
        self.wiwo = _profile.get("status",self.wiwo)
        self.country = _profile.get("country",self.country)

    @property
    def _is_me(self) -> bool:
        from . import session
        if isinstance(self.Session,session.Session):
            if self.Session.username == self.username:
                return True
        return False
    
    def _is_me_raise(self):
        if not self._is_me:
            raise exception.NoPermission
    
    def __int__(self) -> int: return self.id
    def __eq__(self,value) -> bool: return isinstance(value,User) and self.id == value.id
    def __lt__(self,value) -> bool: return isinstance(value,User) and self.id < value.id
    def __ne__(self,value) -> bool: return isinstance(value,User) and self.id > value.id
    def __le__(self,value) -> bool: return isinstance(value,User) and self.id <= value.id
    def __ge__(self,value) -> bool: return isinstance(value,User) and self.id >= value.id

    def get_icon_url(self,size:int=90) -> str:
        common.no_data_checker(self.id)
        return f"https://uploads.scratch.mit.edu/get_image/user/{self.id}_{size}x{size}.png"
    
    async def load_website(self,reload:bool=False) -> common.Response:
        if reload or (self._website_data is None):
            self._website_data = await self.ClientSession.get(f"https://scratch.mit.edu/users/{self.username}/")
        return self._website_data
    
    async def exist(self,use_cache:bool=True) -> bool|None:
        await self.load_website(not use_cache)
        if self._website_data.status_code in [200]:
            return True
        elif self._website_data.status_code in [404]:
            return False
        
    async def is_new_scratcher(self,use_cache:bool=True) -> bool:
        await self.load_website(not use_cache)
        text = self._website_data.text
        return "new scratcher" in text[text.rindex('<span class="group">'):][:70].lower()
    
    async def message_count(self) -> int:
        return (await self.ClientSession.get(
            f"https://api.scratch.mit.edu/users/{self.username}/messages/count/?cachebust={random.randint(0,10000)}"
        )).json()["count"]
    
    class user_featured_data(TypedDict):
        label:str
        title:str
        id:int
        object:project.Project
    
    async def featured_data(self) -> user_featured_data:
        jsons = (await self.ClientSession.get(
            f"https://scratch.mit.edu/site-api/users/all/{self.username}/"
        )).json()
        _project = project.create_Partial_Project(jsons["featured_project_data"]["id"],self)
        _project.title = jsons["featured_project_data"]["title"]
        return {
            "label":jsons["featured_project_label_name"],
            "title":jsons["featured_project_data"]["title"],
            "id":jsons["featured_project_data"]["id"],
            "object":_project
        }
    
    async def follower_count(self) -> int:
        return base.get_count(self.ClientSession,f"https://scratch.mit.edu/users/{self.username}/followers/","Followers (", ")")
    
    def followers(self, *, limit=40, offset=0) -> AsyncGenerator["User", None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/users/{self.username}/followers/",
            None,User,self.Session,limit=limit,offset=offset
        )
    
    async def following_count(self) -> int:
        return base.get_count(self.ClientSession,f"https://scratch.mit.edu/users/{self.username}/following/","Following (", ")")
    
    def following(self, *, limit=40, offset=0) -> AsyncGenerator["User", None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/users/{self.username}/following/",
            None,User,self.Session,limit=limit,offset=offset
        )
    
    async def is_following(self,username:str) -> bool:
        async for i in self.following(limit=common.BIG):
            if i.username.lower() == username.lower():
                return True
        return False
    
    async def is_followed(self,username:str) -> bool:
        async for i in self.followers(limit=common.BIG):
            if i.username.lower() == username.lower():
                return True
        return False
    

    async def project_count(self) -> int:
        return base.get_count(self.ClientSession,f"https://scratch.mit.edu/users/{self.username}/projects/","Shared Projects (", ")")
    
    def projects(self, *, limit=40, offset=0) -> AsyncGenerator[project.Project, None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/users/{self.username}/projects/",
            None,project.Project,self.Session,limit=limit,offset=offset
        )
    
    async def favorite_count(self) -> int:
        return base.get_count(self.ClientSession,f"https://scratch.mit.edu/users/{self.username}/favorites/","Favorites (", ")")
    
    def favorites(self, *, limit=40, offset=0) -> AsyncGenerator[project.Project, None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/users/{self.username}/favorites/",
            None,project.Project,self.Session,limit=limit,offset=offset
        )
    
    async def love_count(self) -> int:
        return base.get_count(self.ClientSession,f"https://scratch.mit.edu/projects/all/{self.username}/loves/","</a>&raquo;\n\n (",")")
    
    async def loves(self, *, start_page=1, end_page=1) -> AsyncGenerator[project.Project, None]:
        for i in range(start_page,end_page+1):
            r = await self.ClientSession.get(f"https://scratch.mit.edu/projects/all/{self.username}/loves/?page={i}",check=False)
            if r.status_code == 404:
                return
            soup = bs4.BeautifulSoup(r.text, "html.parser")
            projects:bs4.element.ResultSet[bs4.element.Tag] = soup.find_all("li", {"class": "project thumb item"})
            if len(projects) == 0:
                return
            for _project in projects:
                _ptext = str(_project)
                id = common.split_int(_ptext,"a href=\"/projects/","/")
                title = common.split(_ptext,f"<span class=\"title\">\n<a href=\"/projects/{id}/\">","</a>")
                author_name = common.split(_ptext,f"by <a href=\"/users/","/")
                _obj = project.Project(self.ClientSession,id,self.Session)
                _obj._update_from_dict({
                    "author":{"username":author_name},
                    "title":title
                })
                yield _obj

    async def activity(self,limit=1000) -> AsyncGenerator[activity.Activity, None]:
        r = await self.ClientSession.get(f"https://scratch.mit.edu/messages/ajax/user-activity/?user={self.username}&max={limit}")
        souplist = bs4.BeautifulSoup(r.text, 'html.parser').find_all("li")
        for i in souplist:
            _obj = activity.Activity(self.ClientSession)
            _obj._update_from_user(self,i)
            yield _obj
        return


    
    async def get_comment_by_id(self,id:int,start:int=1) -> comment.UserComment:
        async for i in self.get_comments(start_page=start,end_page=67):
            if id == i.id:
                return i
            for r in i._reply_cache:
                if id == r.id:
                    return r
        raise exception.CommentNotFound(comment.UserComment,ValueError)

    
    async def get_comments(self, *, start_page=1, end_page=1) -> AsyncGenerator[comment.UserComment, None]:
        # From Scratchattach
        # 404 - NotFound "Comment" (ex:page>67)
        # 503 - NotFound "User"
        if end_page > 67:
            end_page = 67
        for i in range(start_page,end_page+1):
            r = await self.ClientSession.get(f"https://scratch.mit.edu/site-api/comments/user/{self.username}/?page={i}",check=False)
            if r.status_code == 404:
                return
            if r.status_code == 503:
                raise exception.UserNotFound(User,exception.ServerError(503,r))
            soup = bs4.BeautifulSoup(r.text, "html.parser")
            comments:bs4.element.ResultSet[bs4.element.Tag] = soup.find_all("li", {"class": "top-level-reply"})

            for _comment in comments:
                id = int(_comment.find("div", {"class": "comment"})['data-comment-id'])
                userdata = _comment.find("a", {"id": "comment-user"})
                username:str = userdata['data-comment-user']
                userid = int(userdata.find("img",{"class":"avatar"})["src"].split("user/")[1].split("_")[0])
                content = str(_comment.find("div", {"class": "content"}).text).strip()
                send_dt = _comment.find("span", {"class": "time"})['title']

                main = comment.UserComment(self,self.ClientSession,self.Session)
                replies:bs4.element.ResultSet[bs4.element.Tag] = _comment.find_all("li", {"class": "reply"})
                replies_obj:list[comment.UserComment] = []
                for reply in replies:
                    r_id = int(reply.find("div", {"class": "comment"})['data-comment-id'])
                    r_userdata = reply.find("a", {"id": "comment-user"})
                    r_username:str = r_userdata['data-comment-user']
                    r_userid = int(r_userdata.find("img",{"class":"avatar"})["src"].split("user/")[1].split("_")[0])
                    r_content = str(reply.find("div", {"class": "content"}).text).strip()
                    r_send_dt = reply.find("span", {"class": "time"})['title']
                    reply_obj = comment.UserComment(self,self.ClientSession,self.Session)
                    reply_obj._update_from_dict({
                        "id":r_id,"parent_id":id,"commentee_id":None,"content":r_content,"sent_dt":r_send_dt,"author":{"username":r_username,"id":r_userid},"_parent_cache":main,"reply_count":0,"page":i
                    })
                    replies_obj.append(reply_obj)

                main._update_from_dict({
                    "id":id,"parent_id":None,"commentee_id":None,"content":content,"sent_dt":send_dt,
                    "author":{"username":username,"id":userid},
                    "_reply_cache":replies_obj,"reply_count":len(replies_obj),"page":i
                })
                yield main
        return
    
    async def post_comment(self, content, *, parent_id="", commentee_id="") -> comment.UserComment:
        self.has_session_raise()
        data = {
            "commentee_id": commentee_id,
            "content": str(content),
            "parent_id": parent_id,
        }
        text = (await self.ClientSession.post(
            f"https://scratch.mit.edu/site-api/comments/user/{self.username}/add/",json=data
        )).text
        c = comment.UserComment(self,self.ClientSession,self.Session)
        c._update_from_dict({
            "id":common.split_int(text,"data-comment-id=\"","\">"),
            "parent_id":None if parent_id == "" else parent_id,
            "commentee_id":None if commentee_id == "" else commentee_id,
            "datetime_create":common.split(text,"<span class=\"time\" title=\"","\">"),
            "content":content,
            "author":{
                "username":common.split(text,"data-comment-user=\"","\">"),
                "id":common.split_int(text,"src=\"//cdn2.scratch.mit.edu/get_image/user/","_")
            },
            "_reply_cache":[],"reply_count":0,"page":1
        })
        return c
    

    async def toggle_comment(self) -> bool:
        self._is_me_raise()
        r = await self.ClientSession.post(f"https://scratch.mit.edu/site-api/comments/user/{self.username}/toggle-comments/")
        return r.text == "ok"
    
    async def edit(
            self,
            about_me:str|None=None,
            wiwo:str|None=None,
            featured_project_id:int|None=None,
            featured_label:Literal["Featured","ProjectFeatured","Tutorial","Work In Progress","Remix This!","My Favorite Things","Why I Scratch"]|None=None
        ):
        self._is_me_raise()
        data = {
            "comments_allowed":True,
            "id":self.username,
            "status":self.wiwo if wiwo is None else wiwo,
            "thumbnail_url":self.get_icon_url().split("https"),
            "userId":self.id,
            "username":self.username,
        }
        if about_me is not None: data["bio"] = about_me
        if wiwo is not None: data["status"] = wiwo
        if featured_project_id is not None: data["featured_project"] = featured_project_id
        if featured_label is not None: data["featured_project_label_name"] = featured_label
        print(data)
        await self.ClientSession.put(
            f"https://scratch.mit.edu/site-api/users/all/{self.username}/",
            json = data
        )

    async def follow(self,follow:bool=True):
        self.has_session_raise()
        if follow:
            await self.ClientSession.put(f"https://scratch.mit.edu/site-api/users/followers/{self.username}/add/?usernames={self.Session.username}")
        else:
            await self.ClientSession.put(f"https://scratch.mit.edu/site-api/users/followers/{self.username}/remove/?usernames={self.Session.username}")




async def get_user(username:str,*,ClientSession=None) -> User:
    ClientSession = common.create_ClientSession(ClientSession)
    return await base.get_object(ClientSession,username,User)

def create_Partial_User(username:str,user_id:int|None=None,*,ClientSession:common.ClientSession|None=None,session:"session.Session|None"=None) -> User:
    ClientSession = common.create_ClientSession(ClientSession)
    _user = User(ClientSession,username,session)
    if user_id is not None:
        _user.id = common.try_int(user_id)
    return _user

