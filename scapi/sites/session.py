from typing import Any
import zlib
import base64
import json
import datetime
from ..utils import client, common, error, file
from . import base,project,user,studio
from ..utils.types import (
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
    """
    アカウントのステータスを表す。
    
    Attributes:
        session (Session): ステータスを表しているアカウントのセッション
        banned (bool): アカウントがブロックされているか
        should_vpn (bool)
        thumbnail_url (str): アカウントのアイコンのURL
        email (str): アカウントのメールアドレス
        birthday (datetime.date): アカウントに登録された誕生日。日付は常に`1`です
        gender (str): アカウントに登録された性別
        classroom_id (int|None): 生徒アカウントの場合、所属しているクラス

        admin (bool): ScratchTeamのアカウントか
        scratcher (bool): Scratcherか
        new_scratcher (bool): New Scratcherか
        invited_scratcher (bool): Scratcherへの招待が届いているか
        social (bool)
        educator (bool): 教師アカウントか
        educator_invitee (bool)
        student (bool): 生徒アカウントか
        mute_status (bool): アカウントのコメントのミュートステータス

        must_reset_password (bool): パスワードを再設定する必要があるか
        must_complete_registration (bool): アカウント情報を登録する必要があるか
        has_outstanding_email_confirmation (bool)
        show_welcome (bool)
        confirm_email_banner (bool)
        unsupported_browser_banner (bool)
        with_parent_email (bool): 親のメールアドレスで登録しているか
        project_comments_enabled (bool)
        gallery_comments_enabled (bool)
        userprofile_comments_enabled (bool)
        everything_is_totally_normal (bool)
    """
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
    def joined_at(self) -> datetime.datetime:
        """
        Returns:
            datetime.datetime: Scratchに参加した時間
        """
        return common.dt_from_isoformat(self._joined_at,False)


class Session(base._BaseSiteAPI[str]):
    """
    ログイン済みのアカウントを表す

    Attributes:
        session_id (str): アカウントのセッションID
        status (common.MAYBE_UNKNOWN[SessionStatus]): アカウントのステータス
        xtoken (str): アカウントのXtoken
        username (str): ユーザー名
        login_ip (str): ログイン時のIPアドレス
        user (user.User): ログインしているユーザー
    """
    def __repr__(self) -> str:
        return f"<Session username:{self.username}>"

    def __init__(self,session_id:str,_client:client.HTTPClient|None=None):
        self.client = _client or client.HTTPClient()

        super().__init__(self)
        self.session_id:str = session_id
        self.status:common.MAYBE_UNKNOWN[SessionStatus] = common.UNKNOWN
        
        decoded,login_dt = decode_session(self.session_id)

        self.xtoken = decoded.get("token")
        self.username = decoded.get("username")
        self.login_ip = decoded.get("login-ip")
        self.user_id = common.try_int(decoded.get("_auth_user_id"))
        self._logged_at = login_dt

        self.user:user.User = user.User(self.username,self)
        self.user.id = self.user_id or common.UNKNOWN

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
        if self.status:
            self.status.update(data)
        else:
            self.status = SessionStatus(self,data)
        self.user.id = self.user_id or common.UNKNOWN
    
    @property
    def logged_at(self) -> datetime.datetime:
        """
        アカウントにログインした時間を取得する。

        Returns:
            datetime.datetime: ログインした時間
        """
        return common.dt_from_timestamp(self._logged_at,False)
    
    async def logout(self):
        """
        アカウントからログアウトする。

        リクエストが無意味な可能性があります。
        """
        await self.client.post(
            "https://scratch.mit.edu/accounts/logout/",
            json={"csrfmiddlewaretoken":"a"}
        )
    
    async def create_project(
            self,title:str|None=None,
            project_data:file.File|dict|str|bytes|None=None,
            *,
            remix_id:int|None=None,
            is_json:bool|None=None
            
        ) -> "project.Project":
        """
        プロジェクトを作成する

        Args:
            title (str | None, optional): プロジェクトのタイトル
            project_data (file.File | dict | str | bytes | None, optional): プロジェクトのデータ
            remix_id (int | None, optional): リミックスする場合、リミックス元のプロジェクトID
            is_json (bool | None, optional): プロジェクトのデータがjsonか

        Raises:
            error.InvalidData: 作成されたプロジェクトのIDが読み取れませんでした

        Returns:
            project.Project: 作成されたプロジェクト
        """
        param = {}
        if remix_id:
            param["is_remix"] = 1
            param["original_id"] = remix_id
        else:
            param["is_remix"] = 0
        
        if title:
            param["title"] = title

        project_data = project_data or common.empty_project_json
        if isinstance(project_data,dict):
            project_data = json.dumps(project_data)
        if isinstance(project_data,(bytes, bytearray, memoryview)):
            is_json = False
        elif isinstance(project_data,str):
            is_json = True

        async with file._file(project_data) as f:
            content_type = "application/json" if is_json else "application/zip"
            headers = self.client.scratch_headers | {"Content-Type": content_type}
            response = await self.client.post(
                f"https://projects.scratch.mit.edu/",
                data=f.fp,headers=headers,params=param
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
        """
        プロジェクトを取得する。

        Args:
            project_id (int): 取得したいプロジェクトのID

        Returns:
            project.Project: 取得したプロジェクト
        """
        return await project.Project._create_from_api(project_id,self.session)
    
    async def get_studio(self,studio_id:int) -> "studio.Studio":
        """
        スタジオを取得する。

        Args:
            studio_id (int): 取得したいスタジオのID

        Returns:
            studio.Studio: 取得したスタジオ
        """
        return await studio.Studio._create_from_api(studio_id,self.session)
    
    async def get_user(self,username:str) -> "user.User":
        """
        ユーザーを取得する。

        Args:
            username (str): 取得したいユーザーの名前

        Returns:
            user.User: 取得したユーザー
        """
        return await user.User._create_from_api(username,self.session)
    
def session_login(session_id:str) -> common._AwaitableContextManager[Session]:
    """
    セッションIDからアカウントにログインする。

    async with または await でSessionを取得できます。

    Args:
        session_id (str): _description_

    Raises:
        error.HTTPError: 不明な理由でログインに失敗した。
        ValueError: 無効なセッションID。

    Returns:
        common._AwaitableContextManager[Session]: await か async with で取得できるセッション。
    """
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
    """_summary_

    _extended_summary_

    Args:
        username (str): ユーザー名
        password (str): パスワード
        load_status (bool, optional): アカウントのステータスを取得するか。デフォルトはTrueです。
        recaptcha_code (str | None, optional)

    Raises:
        error.LoginFailure: ログインに失敗した。
        error.HTTPError: 不明な理由でログインに失敗した。

    Returns:
        common._AwaitableContextManager[Session]: await か async with で取得できるセッション
    """
    return common._AwaitableContextManager(_login(username,password,load_status,recaptcha_code=recaptcha_code))