from typing import Any
import zlib
import base64
import json
import datetime
from ..others import client, common, error
from . import base,project,user,studio
from ..others.types import (
    DecodedSessionID,
    SessionStatusPayload,
    ProjectServerPayload
)

def decode_session(session_id:str) -> tuple[DecodedSessionID,int]:
    s1,s2,s3 = session_id.strip('".').split(':')

    padding = '=' * (-len(s1) % 4)
    compressed = base64.urlsafe_b64decode(s1 + padding)
    decompressed = zlib.decompress(compressed)
    return json.loads(decompressed.decode('utf-8')),common.b62decode(s2)

class SessionStatus:
    def __init__(self,session:"Session",data:SessionStatusPayload):
        self.session = session
        self.update(data)

    def update(self,data:SessionStatusPayload):
        _user = data.get("user")
        self.session.user_id = _user.get("id")
        self.banned = _user.get("banned")
        self.should_vpn = _user.get("should_vpn")
        self.session.username = _user.get("username")
        self.session.xtoken = _user.get("token")
        self.thumbnail_url = _user.get("thumbnailUrl")
        self._joined_at = _user.get("dateJoined")
        self.email = _user.get("email")
        self.birthday = datetime.date(_user.get("birthYear"),_user.get("birthMonth"),1)
        self.gender = _user.get("gender")
        self.classroom_id = _user.get("classroomId")

        _permission = data.get("permissions")
        self.admin = _permission.get("admin")
        self.scratcher = _permission.get("scratcher")
        self.new_scratcher = _permission.get("new_scratcher")
        self.invited_scratcher = _permission.get("invited_scratcher")
        self.social = _permission.get("social")
        self.educator = _permission.get("educator")
        self.educator_invitee = _permission.get("educator_invitee")
        self.student = _permission.get("student")
        self.mute_status = _permission.get("mute_status")

        _flags = data.get("flags")
        self.must_reset_password = _flags.get("must_reset_password")
        self.must_complete_registration = _flags.get("must_complete_registration")
        self.has_outstanding_email_confirmation = _flags.get("has_outstanding_email_confirmation")
        self.show_welcome = _flags.get("show_welcome")
        self.confirm_email_banner = _flags.get("confirm_email_banner")
        self.unsupported_browser_banner = _flags.get("unsupported_browser_banner")
        self.with_parent_email = _flags.get("with_parent_email")
        self.project_comments_enabled = _flags.get("project_comments_enabled")
        self.gallery_comments_enabled = _flags.get("gallery_comments_enabled")
        self.userprofile_comments_enabled = _flags.get("userprofile_comments_enabled")
        self.everything_is_totally_normal = _flags.get("everything_is_totally_normal")

    @property
    def joined_at(self):
        return common.dt_from_isoformat(self._joined_at,False)


class Session(base._BaseSiteAPI[str]):
    def __repr__(self) -> str:
        return f"<Session username:{self.username}>"

    def __init__(self,session_id:str,_client:client.HTTPClient|None=None):
        self.client = _client or client.HTTPClient()

        super().__init__(self)
        self.session_id:str = session_id
        self._status:SessionStatus|None = None
        
        decoded,login_dt = decode_session(self.session_id)

        self.xtoken = decoded.get("token")
        self.username = decoded.get("username")
        self.login_ip = decoded.get("login-ip")
        self.user_id = common.try_int(decoded.get("_auth_user_id"))
        self._logged_at = login_dt

        self.user:user.User = user.User(self.username,self)
        self.user.id = self.user_id

        self.client.scratch_cookies = {
            "scratchsessionsid": session_id,
            "scratchcsrftoken": "a",
            "scratchlanguage": "en",
        }
        self.client.scratch_headers["X-token"] = self.xtoken
    
    async def update(self):
        response = await self.client.get("https://scratch.mit.edu/session/")
        try:
            data:SessionStatusPayload = response.json()
            self._update_from_data(data)
        except Exception:
            raise error.InvalidData(response)
        self.client.scratch_headers["X-token"] = self.xtoken
    
    def _update_from_data(self, data:SessionStatusPayload):
        if data.get("user") is None:
            raise ValueError()
        if self._status:
            self._status.update(data)
        else:
            self._status = SessionStatus(self,data)
        self.user.id = self.user_id
    
    @property
    def logged_at(self):
        return common.dt_from_timestamp(self._logged_at,False)
    
    @property
    def is_scratcher(self) -> None | bool:
        return self._status and self._status.scratcher
    
    @property
    def is_verified_educator(self) -> None | bool:
        return self._status and self._status.educator and (not self._status.invited_scratcher)
    
    async def logout(self):
        await self.client.post(
            "https://scratch.mit.edu/accounts/logout/",
            json={"csrfmiddlewaretoken":"a"}
        )
    
    async def create_project(self,title:str|None=None,project_json:Any=None,*,remix_id:int|None=None):
        param = {}
        if remix_id:
            param["is_remix"] = 1
            param["original_id"] = remix_id
        else:
            param["is_remix"] = 0
        
        if title:
            param["title"] = title

        project_json = project_json or common.empty_project_json
        if isinstance(project_json,dict):
            _data = json.dumps(project_json)
            content_type = "application/json"
        elif isinstance(project_json,str):
            _data = project_json
            content_type = "application/json"
        elif isinstance(project_json,bytes):
            _data = project_json
            content_type = "application/zip"
        else:
            raise TypeError()
        headers = self.client.scratch_headers|{"Content-Type": content_type}
        
        response = await self.client.post(
            "https://projects.scratch.mit.edu/",
            params=param,data=_data,headers=headers
        )

        data:ProjectServerPayload = response.json()
        project_id = data.get("content-name")
        if not project_id:
            raise error.InvalidData(response)
        
        _project = project.Project(int(project_id),self)
        _project.author = self.user
        b64_title = data.get("content-title")
        if b64_title:
            _project.title = base64.b64decode(b64_title).decode()

        return _project
    
    async def get_project(self,project_id:int) -> "project.Project":
        return await project.Project._create_from_api(project_id,self.session)
    
    async def get_studio(self,studio_id:int) -> "studio.Studio":
        return await studio.Studio._create_from_api(studio_id,self.session)
    
    async def get_user(self,username:str) -> "user.User":
        return await user.User._create_from_api(username,self.session)
    
def session_login(session_id:str) -> common._AwaitableContextManager[Session]:
    return common._AwaitableContextManager(Session._create_from_api(session_id))

async def _login(
        username:str,
        password:str,
        load_status:bool=True,
        *,
        recaptcha_code:str|None=None
    ):
    _client = client.HTTPClient()
    data = {"username":username,"password":password}
    if recaptcha_code:
        login_url = "https://scratch.mit.edu/login_retry/"
        data["g-recaptcha-response"] = recaptcha_code
    else:
        login_url = "https://scratch.mit.edu/login/"
    try:
        response = await _client.post(
            login_url,
            json=data,
            cookies={
                "scratchcsrftoken" : "a",
                "scratchlanguage" : "en",
            }
        )
    except error.Forbidden as e:
        await _client.close()
        if type(e) is not error.Forbidden:
            raise
        raise error.LoginFailure(e.response) from None
    except:
        await _client.close()
        raise
    set_cookie = response._response.headers.get("Set-Cookie","")
    session_id = common.split(set_cookie,"scratchsessionsid=\"","\"")
    if not session_id:
        raise error.LoginFailure(response)
    if load_status:
        return await Session._create_from_api(session_id,_client)
    else:
        return Session(session_id,_client)
    
def login(username:str,password:str,load_status:bool=True,*,recaptcha_code:str|None=None) -> common._AwaitableContextManager[Session]:
    return common._AwaitableContextManager(_login(username,password,load_status,recaptcha_code=recaptcha_code))