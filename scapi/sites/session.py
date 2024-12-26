import asyncio
import datetime
import re
from typing import AsyncGenerator
import warnings

from ..others import other_api
from ..others import common
from ..others import error as exception
from . import user,project,studio,activity,base


class SessionStatus:
    def __init__(self,response_json:dict[str,dict]):
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
        self.update(response_json)

    def update(self,response_json:dict[str,dict]):
        for _,v1 in response_json.items():
            for k2,v2 in v1.items():
                setattr(self,k2,v2)

        try:
            self.joined_dt = common.to_dt(self.dateJoined)
        except Exception:
            pass

class Session(base._BaseSiteAPI):
    raise_class = exception.SessionNotFound
    id_name = "session_id"

    def __str__(self):
        return f"<Session Username:{self.username}>"


    def __init__(
        self,
        ClientSession:common.ClientSession,
        session_id:str,
        **entries
    ):
        super().__init__("post","https://scratch.mit.edu/session",ClientSession,self)

        self.ClientSession._cookie = {
            "scratchsessionsid" : session_id,
            "scratchcsrftoken" : "a",
            "scratchlanguage" : "en",
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        self.status:SessionStatus = None
        self.session_id:str = session_id
        self.xtoken:str|None = ""
        self.is_email_verified:bool|None = None
        self.email:str|None = None
        self.new_scratcher:bool|None = None
        self.mute_status:dict|None = None
        self.username:str|None = None
        self.banned:bool|None = None

    def _update_from_dict(self,data):
        self.status = SessionStatus(data)
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

    
    async def logout(self) -> None:
        await self.ClientSession.post(
            "https://scratch.mit.edu/accounts/logout/",
            json={"csrfmiddlewaretoken":other_api.get_csrf_token_sync()}
        )
        await self.ClientSession.close()
    
    async def me(self) -> user.User:
        return await base.get_object(self.ClientSession,self.username,user.User,self)
    
    def create_Partial_myself(self) -> user.User:
        _user = user.create_Partial_User(self.username,self.status.id,ClientSession=self.ClientSession,session=self)
        _user._join_date = self.status.dateJoined
        _user.join_date = self.status.joined_dt
        return _user
    
    async def create_project(self,title:str|None=None,project_json:dict|None=None,remix_id:int|None=None) -> project.Project:
        if project_json is None:
            project_json = common.empty_project_json.copy()
        if title is None:
            title = "Untitled"
        
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
        raise exception.ResponseError(response.status_code,response)
    
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
                _obj = activity.Activity(self.ClientSession)
                _obj._update_from_message(self,j)
                yield _obj
    
    async def get_project(self,project_id:int) -> project.Project:
        return await base.get_object(self.ClientSession,project_id,project.Project,self)
    
    async def get_user(self,username:str) -> user.User:
        return  await base.get_object(self.ClientSession,username,user.User,self)
    
    async def get_studio(self,studio_id:int) -> studio.Studio:
        return  await base.get_object(self.ClientSession,studio_id,studio.Studio,self)
    
async def session_login(session_id,*,ClientSession=None) -> Session:
    ClientSession = common.create_ClientSession(ClientSession)
    return await base.get_object(ClientSession,session_id,Session)


async def login(username,password) -> Session:
    ClientSession = common.create_ClientSession()
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
            ClientSession=ClientSession
        )
    except Exception as e:
        raise exception.LoginFailure(e)