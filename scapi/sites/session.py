import datetime
import re
from typing import TYPE_CHECKING, AsyncGenerator,Literal, TypedDict
import warnings
import hashlib
import json

import aiohttp

from scapi.cloud.cloud import ScratchCloud

from ..others import common
from ..others import error as exception
from . import user,project,studio,activity,base,forum,classroom,asset

if TYPE_CHECKING:
    from ..event.message import SessionMessageEvent


class SessionStatus:
    def __init__(self):
        self.confirm_email_banner:bool = None
        self.everything_is_totally_normal:bool = None
        self.gallery_comments_enabled:bool = None
        self.has_outstanding_email_confirmation:bool = None
        self.must_complete_registration:bool = None
        self.must_reset_password:bool = None
        self.project_comments_enabled:bool = None
        self.show_welcome:bool = None
        self.unsupported_browser_banner:bool = None
        self.userprofile_comments_enabled:bool = None
        self.with_parent_email:bool = None

        self.admin:bool = None
        self.educator:bool = None
        self.educator_invitee:bool = None
        self.invited_scratcher:bool = None
        self.mute_status:dict = {}
        self.new_scratcher:bool = None
        self.scratcher:bool = None
        self.social:bool = None
        self.student:bool = None

        self.banned:bool = None
        self.birthMonth:int = None
        self.birthYear:int = None
        self.classroomId:int|None = None
        self.dateJoined:str = None
        self.email:str = None
        self.gender:str = None
        self.id:int = None
        self.should_vpn:bool = None
        self.thumbnailUrl:str = None
        self.token:str = None
        self.username:str = None

        self.joined_dt:datetime.datetime = None

    def update(self,response_json:dict[str,dict]):
        for _,v1 in response_json.items():
            for k2,v2 in v1.items():
                setattr(self,k2,v2)

        try:
            self.joined_dt = common.to_dt(self.dateJoined)
        except Exception:
            pass

class Session(base._BaseSiteAPI):
    id_name = "session_id"

    def __repr__(self):
        return f"<Session Username:{self.username}>"
    
    def __eq__(self, other:"Session"):
        return isinstance(other,Session) and self.session_id == other.session_id


    def __init__(
        self,
        ClientSession:common.ClientSession,
        session_id:str,
        **entries
    ):
        self._ClientSession = ClientSession
        super().__init__("get","https://scratch.mit.edu/session/",ClientSession,self)

        self.ClientSession._cookie = {
            "scratchsessionsid" : session_id,
            "scratchcsrftoken" : "a",
            "scratchlanguage" : "en",
        }
        self.status:SessionStatus = None
        self.session_id:str = session_id
        self.xtoken:str = ""
        self.is_email_verified:bool = None
        self.email:str = None
        self.scratcher:bool = None
        self.mute_status:dict|None = None
        self.username:str = None
        self.banned:bool = None

        self._user:user.User|None = None

    def _update_from_dict(self,data:dict):
        self.status = self.status or SessionStatus()
        self.status.update(data)
        self.xtoken = self.status.token
        self.email = self.status.email
        self.scratcher = self.status.scratcher
        self.mute_status = self.status.mute_status
        self.username = self.status.username
        self.banned = self.status.banned
        self.ClientSession._header = self.ClientSession._header|{"X-Token":str(self.xtoken)}
        if self.banned:
            warnings.warn(f"Warning: {self.username} is BANNED.")
        if self.status.has_outstanding_email_confirmation:
            warnings.warn(f"Warning: {self.username} is not email confirmed.")

    
    def session_decode(self) -> dict:
        import zlib
        import base64
        import json
        session_id = self.session_id.strip('".')
        session_id = session_id.split(':')[0]
        padding = '=' * (-len(session_id) % 4)
        compressed = base64.urlsafe_b64decode(session_id + padding)
        decompressed = zlib.decompress(compressed)
        return json.loads(decompressed.decode('utf-8'))

    async def logout(self) -> None:
        await self.ClientSession.post(
            "https://scratch.mit.edu/accounts/logout/",
            json={"csrfmiddlewaretoken":"a"}
        )
        await self.ClientSession.close()

    async def change_password(self,old_password:str|None,new_password:str):
        if self.status.must_reset_password and self.check:
            old_password = None
        if old_password is None:
            if not self.status.must_reset_password and self.check:
                raise exception.NoPermission()
            data = aiohttp.FormData({
                "csrfmiddlewaretoken":"a",
                "new_password1":new_password,
                "new_password2":new_password
            })
            r = await self.ClientSession.post(
                "https://scratch.mit.edu/classes/student_password_reset/",
                data=data
            )
            if r.url == "https://scratch.mit.edu/classes/student_password_reset/":
                raise exception.BadResponse(r)
        else:
            data = json.dumps({
                "csrfmiddlewaretoken": "a",
                "old_password": old_password,
                "new_password1": new_password,
                "new_password2": new_password
            })
            r = await self.ClientSession.post(
                "https://scratch.mit.edu/accounts/password_change/",
                data=data
            )
            if r.url == "https://scratch.mit.edu/accounts/password_change/":
                raise exception.BadResponse(r)
    
        
    async def change_country(self,country:str):
        await self.ClientSession.post(
            "https://scratch.mit.edu/accounts/settings/",
            data={"country": country}
        )
    
    async def change_email(self,password:str,email:str):
        await self.ClientSession.post(
            "https://scratch.mit.edu/accounts/email_change/",
            data={
                "email_address": email,
                "password": password
            }
        )

    async def register_info(self,password:str,birth_day:datetime.date,gender:str,country:str):
        if (not self.status.must_complete_registration) and self.check:
            raise exception.NoPermission()
        data = aiohttp.FormData({
            "birth_month":str(birth_day.month),
            "birth_year":str(birth_day.year),
            "gender":gender,
            "country":country,
            "is_robot":"false",
            "password":password
        })
        r = await self.ClientSession.post("https://scratch.mit.edu/classes/student_update_registration/",data=data)


    async def delete_account(self,password:str,delete_project:bool):
        r = await self.ClientSession.post(
            "https://scratch.mit.edu/accounts/settings/delete_account/",
            data={
                "delete_state": "delbyusrwproj" if delete_project else "delbyusr",
                "password": password
            }
        )
        d = r.json()
        if not d.get("success"):
            raise exception.BadResponse(r)
    
    async def me(self) -> user.User:
        self._user = await base.get_object(self.ClientSession,self.username,user.User,self)
        return self._user
    
    def create_Partial_myself(self) -> user.User:
        self._user = self._user or user.create_Partial_User(self.username,self.status.id,ClientSession=self.ClientSession,session=self)
        self._user._join_date = self.status.dateJoined
        self._user.join_date = self.status.joined_dt
        return self._user
    
    async def my_classroom(self) -> classroom.Classroom|None:
        if self.status.classroomId is None:
            return
        return await base.get_object(self.ClientSession,self.status.classroomId,classroom.Classroom,self)
    
    async def create_project(self,title:str="Untitled",project_json:dict|None=None,remix_id:int|None=None) -> project.Project:
        if project_json is None:
            project_json = common.empty_project_json.copy()
        
        if remix_id is None:
            params = {
                'is_remix': '0',
                'title': title,
            }
        else:
            params = {
                'is_remix': "1",
                'original_id': remix_id,
                'title': title,
            }
        response = await self.ClientSession.post(
            "https://projects.scratch.mit.edu/",
            params=params,json=project_json
        )
        if response.status_code == 200:
            return await base.get_object(
                self.ClientSession,int(response.json()['content-name']),
                project.Project,self.Session
            )
        raise exception.ResponseError(response)
    
    async def create_studio(self) -> studio.Studio:
        if (not self.status.scratcher) and self.check:
            raise exception.NoPermission()
        response = await self.ClientSession.post("https://scratch.mit.edu/studios/create/")
        id = common.split_int(response.json().get("redirect"),"/studios/","/")
        if id is None:
            raise exception.BadResponse(response)
        return await base.get_object(self.ClientSession,id,studio.Studio,self)
    
    async def create_class(self,title:str,about_class:str="",wiwo:str="") -> classroom.Classroom:
        if (not self.status.educator) and self.check:
            raise exception.NoPermission()
        data = {
            "title":title,
            "description":about_class,
            "status":wiwo,
            "is_robot":False,
            "csrfmiddlewaretoken":"a"
        }
        r = await self.ClientSession.post("https://scratch.mit.edu/classes/create_classroom/",json=data)
        data = r.json()
        if not data[0].get("success"):
            raise exception.ResponseError(r)

        return await base.get_object(self.ClientSession,data[0]["id"],classroom.Classroom,self)
    
    async def message(self, *, limit=40, offset=0) -> AsyncGenerator[activity.Activity, None]:
        c = 0
        for i in range(offset,offset+limit,40):
            r = await common.api_iterative(
                self.ClientSession,f"https://api.scratch.mit.edu/users/{self.username}/messages",limit=40,offset=i
            )
            if len(r) == 0: return
            for j in r:
                c = c + 1
                if c == limit: return
                _obj = activity.Activity()
                _obj._update_from_message(self,j)
                yield _obj

    def message_event(self,interval=30) -> "SessionMessageEvent":
        from ..event.message import SessionMessageEvent
        return SessionMessageEvent(self,interval)
    
    async def message_count(self) -> int:
        r = await self.ClientSession.get("https://scratch.mit.edu/messages/ajax/get-message-count/")
        return r.json().get("msg_count")
    
    async def clear_message(self):
        await self.ClientSession.post("https://scratch.mit.edu/site-api/messages/messages-clear/")

    class scratcher_invite(TypedDict):
        id:int
        datetime_created:str
        unread:int
        actor_id:int
        invitee_id:int

    async def check_scratcher_invite(self) -> scratcher_invite|None:
        r = await self.ClientSession.get(f"https://api.scratch.mit.edu/users/{self.username}/invites")
        return r.json() or None
    
    async def become_scratcher(self):
        if self.check and not self.status.invited_scratcher:
            raise exception.NoPermission()
        await self.ClientSession.get(f"https://scratch.mit.edu/users/{self.username}/promote-to-scratcher/")

    async def following_feed(self, *, limit=40, offset=0) -> AsyncGenerator[activity.Activity, None]:
        c = 0
        for i in range(offset,offset+limit,40):
            r = await common.api_iterative(
                self.ClientSession,f"https://api.scratch.mit.edu/users/{self.username}/following/users/activity",
                limit=40,offset=i
            )
            if len(r) == 0: return
            for j in r:
                c = c + 1
                if c == limit: return
                _obj = activity.Activity()
                _obj._update_from_feed(self,j)
                yield _obj

    def following_loves(self, *, limit=40, offset=0) -> AsyncGenerator[project.Project, None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/users/{self.username}/following/users/loves",
            None, project.Project, self.Session, limit=limit, offset=offset
        )

    def backpack(self, *, limit=40, offset=0) -> AsyncGenerator[asset.Backpack, None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://backpack.scratch.mit.edu/{self.username}",
            None, asset.Backpack, self.Session, limit=limit, offset=offset
        )

    def viewed_projects(self, *, limit=40, offset=0) -> AsyncGenerator[project.Project, None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/users/{self.username}/projects/recentlyviewed",
            None, project.Project, self.Session, limit=limit, offset=offset
        )
    

    # type: all shared notshared trashed
    # sorted: view_count love_count remixers_count title
    def get_mystuff_projects(
            self, start_page:int=1, end_page:int=1, type:str="all", sort:str="", descending:bool=True
        ) -> AsyncGenerator[project.Project, None]:
        add_params = {"descsort":sort} if descending else {"ascsort":sort}
        return base.get_object_iterator(
            self.ClientSession,f"https://scratch.mit.edu/site-api/projects/{type}/",
            "pk",project.Project, self,
            limit=end_page-start_page+1 ,offset=start_page, max_limit=1, is_page=True,
            add_params=add_params,update_func_name="_update_from_mystuff"
        )
    
    get_mystuff_project = common.deprecated("Classroom","get_mystuff_project","get_mystuff_projects")(get_mystuff_projects)
    
    # type: all owned curated
    # sorted: projecters_count title
    def get_mystuff_studios(
            self, start_page:int=1, end_page:int=1, type:str="all", sort:str="", descending:bool=True
        ) -> AsyncGenerator[studio.Studio, None]:
        add_params = {"descsort":sort} if descending else {"ascsort":sort}
        return base.get_object_iterator(
            self.ClientSession,f"https://scratch.mit.edu/site-api/galleries/{type}/",
            "pk",studio.Studio, self,
            limit=end_page-start_page+1 ,offset=start_page, max_limit=1, is_page=True,
            add_params=add_params,update_func_name="_update_from_mystuff"
        )
    
    get_mystuff_project = common.deprecated("Classroom","get_mystuff_studio","get_mystuff_studios")(get_mystuff_projects)
    
    # type: all closed
    # sort: student_count title
    def get_mystuff_classes(
            self, start_page:int=1, end_page:int=1, type:str="all", sort:str="", descending:bool=True
        ) -> AsyncGenerator[classroom.Classroom, None]:
        if self.check and (not self.status.educator):
            raise exception.NoPermission()
        add_params = {"descsort":sort} if descending else {"ascsort":sort}
        return base.get_object_iterator(
            self.ClientSession,f"https://scratch.mit.edu/site-api/classrooms/{type}/",
            "pk",classroom.Classroom, self,
            limit=end_page-start_page+1 ,offset=start_page, max_limit=1, is_page=True,
            add_params=add_params,update_func_name="_update_from_mystuff"
        )
    
    async def get_mystuff_class(self,id:int) -> classroom.Classroom:
        if self.check and (not self.status.educator):
            raise exception.NoPermission()
        r = await self.ClientSession.get(f"https://scratch.mit.edu/site-api/classrooms/all/{id}/")
        _classroom = classroom.Classroom(self.ClientSession,id,self.Session)
        _classroom._update_from_old_dict(r.json())
        return _classroom
    
    def get_mystuff_students(self,start_page:int=1, end_page:int=1) -> AsyncGenerator[user.User, None]:
        if self.check and (not self.status.educator):
            raise exception.NoPermission()
        return base.get_object_iterator(
            self.ClientSession,f"https://scratch.mit.edu/site-api/classrooms/students/of/{self.username}/",
            "pk",user.User, self.Session,
            limit=end_page-start_page+1 ,offset=start_page, max_limit=1, is_page=True,
            update_func_name="_update_from_student_dict"
        )

    
    async def check_educator_password(self,password:str) -> bool:
        if self.check and (not self.status.educator):
            raise exception.NoPermission()
        r = await self.ClientSession.post(
            "https://scratch.mit.edu/site-api/classrooms/check_educator_password/",
            json={"password":password}
        )
        return r.json().get("success")
    
    async def upload_asset(self,data:str|bytes,file_ext:str="") -> str:
        data, file_ext = await common.open_tool(data,file_ext)
        file_ext = file_ext.split(".")[-1]
        asset_id = hashlib.md5(data).hexdigest()

        await self.ClientSession.post(
            f"https://assets.scratch.mit.edu/{asset_id}.{file_ext}",
            data=data,
        )

        return f"{asset_id}.{file_ext}"
    
    async def empty_trash(self,password:str):
        data = {
            "password":password,
            "csrfmiddlewaretoken":"a",
        }
        await self.ClientSession.post(
            "https://scratch.mit.edu/site-api/projects/trashed/empty/",
            json=data
        )

    
    def get_cloud(self,project_id:int) -> "ScratchCloud":
        from ..cloud import cloud
        return cloud.ScratchCloud(project_id,self)
    
    async def get_project(self,project_id:int) -> project.Project:
        return await base.get_object(self.ClientSession,project_id,project.Project,self)
    
    async def get_user(self,username:str) -> user.User:
        return await base.get_object(self.ClientSession,username,user.User,self)
    
    async def get_studio(self,studio_id:int) -> studio.Studio:
        return await base.get_object(self.ClientSession,studio_id,studio.Studio,self)
    
    async def get_forumtopic(self,topic_id:int) -> forum.ForumTopic:
        return await base.get_object(self.ClientSession,topic_id,forum.ForumTopic,self)
    
    async def get_forumpost(self,post_id:int) -> forum.ForumPost:
        return await base.get_object(self.ClientSession,post_id,forum.ForumPost,self)
    
    def explore_projects(self, *, query:str="*", mode:str="trending", language:str="en", limit:int=40, offset:int=0) -> AsyncGenerator["project.Project",None]:
        return base.get_object_iterator(
            self.ClientSession, "https://api.scratch.mit.edu/explore/projects",
            None,project.Project,self,limit=limit,offset=offset,
            add_params={"language":language,"mode":mode,"q":query}
        )

    def search_projects(self, query:str, *, mode:str="trending", language:str="en", limit:int=40, offset:int=0) -> AsyncGenerator["project.Project",None]:
        return base.get_object_iterator(
            self.ClientSession, "https://api.scratch.mit.edu/search/projects",
            None,project.Project,self,limit=limit,offset=offset,
            add_params={"language":language,"mode":mode,"q":query}
        )
    
    def explore_studios(self, *, query:str="*", mode:str="trending", language:str="en", limit:int=40, offset:int=0) -> AsyncGenerator["studio.Studio",None]:
        return base.get_object_iterator(
            self.ClientSession, "https://api.scratch.mit.edu/explore/studios",
            None,studio.Studio,self,limit=limit,offset=offset,
            add_params={"language":language,"mode":mode,"q":query}
        )

    def search_studios(self, query:str, *, mode:str="trending", language:str="en", limit:int=40, offset:int=0) -> AsyncGenerator["studio.Studio",None]:
        return base.get_object_iterator(
            self.ClientSession, "https://api.scratch.mit.edu/search/studios",
            None,studio.Studio,self,limit=limit,offset=offset,
            add_params={"language":language,"mode":mode,"q":query}
        )
    
    async def get_classroom(self,classroom_id:int) -> classroom.Classroom:
        return await base.get_object(self.ClientSession,classroom_id,classroom.Classroom)

    async def get_classroom_by_token(self,classtoken:str) -> classroom.Classroom:
        r = (await self.ClientSession.get(f"https://api.scratch.mit.edu/classtoken/{classtoken}")).json()
        _obj = classroom.Classroom(self.ClientSession,r["id"])
        _obj._update_from_dict(r)
        _obj.classtoken = classtoken
        return _obj
    
    async def link_session(self, *l, **d):
        raise TypeError()
    
async def session_login(session_id:str,*,ClientSession=None) -> Session:
    return await base.get_object(ClientSession,session_id,Session)


async def login(username:str,password:str,*,ClientSession=None) -> Session:
    _created_cs = ClientSession is None
    if _created_cs: ClientSession = common.create_ClientSession()
    try:
        r = await ClientSession.post(
            "https://scratch.mit.edu/login/",
            json={"username":username,"password":password},
            cookie={
                "scratchcsrftoken" : "a",
                "scratchlanguage" : "en",
            }
        )
        return await session_login(
            str(re.search('"(.*)"', r.headers["Set-Cookie"]).group()).replace("\"",""),
            ClientSession=ClientSession if _created_cs else None
        )
    except Exception as e:
        if _created_cs: await ClientSession.close()
        raise exception.LoginFailure(e)
    
async def send_password_reset_email(clientsession:common.ClientSession,username:str="",email:str="") -> None | bool:
    if username is None and email is None:
        raise ValueError
    r = await clientsession.post(
        "https://scratch.mit.edu/accounts/password_reset/",
        data={
            "username":username,
            "email":email,
            "csrfmiddlewaretoken":"a"
        }
    )
    if "t have an account with that" in r.text:
        return False
    if "We've e-mailed instructions for resetting your password to the e-mail address you provided, or the email associated with your account. If you don't receive it shortly, be sure to check your spam folder." in r.text:
        return True
    return None