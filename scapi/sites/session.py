from __future__ import annotations

from typing import AsyncGenerator, Literal
import zlib
import base64
import json
import datetime

import aiohttp
from ..utils.types import (
    DecodedSessionID,
    SessionStatusPayload,
    ProjectServerPayload,
    OldAnyObjectPayload,
    OldProjectPayload,
    OldStudioPayload
)
from ..utils.client import HTTPClient
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    api_iterative,
    page_api_iterative,
    dt_from_isoformat,
    dt_from_timestamp,
    _AwaitableContextManager,
    b62decode,
    try_int,
    split,
    empty_project_json
)
from ..utils.error import (
    ClientError,
    InvalidData,
    Forbidden,
    HTTPError,
    LoginFailure
)
from ..utils.file import File,_file
from ..event.cloud import ScratchCloud
from .base import _BaseSiteAPI

from .project import Project
from .studio import Studio
from .user import User

def decode_session(session_id:str) -> tuple[DecodedSessionID,int]:
    s1,s2,s3 = session_id.strip('".').split(':')

    padding = '=' * (-len(s1) % 4)
    compressed = base64.urlsafe_b64decode(s1 + padding)
    decompressed = zlib.decompress(compressed)
    return json.loads(decompressed.decode('utf-8')),b62decode(s2)

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
        return dt_from_isoformat(self._joined_at,False)


class Session(_BaseSiteAPI[str]):
    """
    ログイン済みのアカウントを表す

    Attributes:
        session_id (str): アカウントのセッションID
        status (MAYBE_UNKNOWN[SessionStatus]): アカウントのステータス
        xtoken (str): アカウントのXtoken
        username (str): ユーザー名
        login_ip (str): ログイン時のIPアドレス
        user (User): ログインしているユーザー
    """
    def __repr__(self) -> str:
        return f"<Session username:{self.username}>"

    def __init__(self,session_id:str,_client:HTTPClient|None=None):
        self.client = _client or HTTPClient()

        super().__init__(self)
        self.session_id:str = session_id
        self.status:MAYBE_UNKNOWN[SessionStatus] = UNKNOWN
        
        decoded,login_dt = decode_session(self.session_id)

        self.xtoken = decoded.get("token")
        self.username = decoded.get("username")
        self.login_ip = decoded.get("login-ip")
        self.user_id = try_int(decoded.get("_auth_user_id"))
        self._logged_at = login_dt

        self.user:User = User(self.username,self)
        self.user.id = self.user_id or UNKNOWN

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
            raise ClientError(response)
        self.client.scratch_headers["X-token"] = self.xtoken
    
    def _update_from_data(self, data:SessionStatusPayload):
        if data.get("user") is None:
            raise ValueError()
        if self.status:
            self.status.update(data)
        else:
            self.status = SessionStatus(self,data)
        self.user.id = self.user_id or UNKNOWN
    
    @property
    def logged_at(self) -> datetime.datetime:
        """
        アカウントにログインした時間を取得する。

        Returns:
            datetime.datetime: ログインした時間
        """
        return dt_from_timestamp(self._logged_at,False)
    
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
            project_data:File|dict|str|bytes|None=None,
            *,
            remix_id:int|None=None,
            is_json:bool|None=None
            
        ) -> "Project":
        """
        プロジェクトを作成する

        Args:
            title (str | None, optional): プロジェクトのタイトル
            project_data (File | dict | str | bytes | None, optional): プロジェクトのデータ本体。
            remix_id (int | None, optional): リミックスする場合、リミックス元のプロジェクトID
            is_json (bool | None, optional): プロジェクトのデータの形式。zip形式を使用したい場合はFalseを指定してください。Noneにすると簡易的に判定されます。

        Returns:
            Project: 作成されたプロジェクト
        """
        param = {}
        if remix_id:
            param["is_remix"] = 1
            param["original_id"] = remix_id
        else:
            param["is_remix"] = 0
        
        if title:
            param["title"] = title

        project_data = project_data or empty_project_json
        if isinstance(project_data,dict):
            project_data = json.dumps(project_data)
        if isinstance(project_data,(bytes, bytearray, memoryview)):
            is_json = False
        elif isinstance(project_data,str):
            is_json = True

        async with _file(project_data) as f:
            content_type = "application/json" if is_json else "application/zip"
            headers = self.client.scratch_headers | {"Content-Type": content_type}
            response = await self.client.post(
                f"https://projects.scratch.mit.edu/",
                data=f.fp,headers=headers,params=param
            )

        data:ProjectServerPayload = response.json()
        project_id = data.get("content-name")
        if not project_id:
            raise InvalidData(response)
        
        project = Project(int(project_id),self)
        project.author = self.user
        b64_title = data.get("content-title")
        if b64_title:
            project.title = base64.b64decode(b64_title).decode()

        return project
    
    async def get_mystuff_projects(
            self,
            start_page:int|None=None,
            end_page:int|None=None,
            type:Literal["all","shared","notshared","trashed"]="all",
            sort:Literal["","view_count","love_count","remixers_count","title"]="",
            descending:bool=True
        ) -> AsyncGenerator[Project]:
        """
        自分の所有しているプロジェクトを取得する。

        Args:
            start_page (int|None, optional): 取得するコメントの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するコメントの終了ページ位置。初期値はstart_pageの値です。
            type (Literal["all","shared","notshared","trashed"], optional): 取得したいプロジェクトの種類。デフォルトは"all"です。
            sort (Literal["","view_count","love_count","remixers_count","title"], optional): ソートしたい順。デフォルトは "" (最終更新順)です。
            descending (bool, optional): 降順にするか。デフォルトはTrueです。

        Yields:
            Project: 取得したプロジェクト
        """
        add_params:dict[str,str|int|float] = {"descsort":sort} if descending else {"ascsort":sort}
        async for _p in page_api_iterative(
            self.client,f"https://scratch.mit.edu/site-api/projects/{type}/",
            start_page,end_page,add_params
        ):
            _p:OldAnyObjectPayload[OldProjectPayload]
            yield Project._create_from_data(_p["pk"],_p["fields"],self,"_update_from_old_data")

    async def get_mystuff_studios(
            self,
            start_page:int|None=None,
            end_page:int|None=None,
            type:Literal["all","owned","curated"]="all",
            sort:Literal["","projecters_count","title"]="",
            descending:bool=True
        ) -> AsyncGenerator[Studio]:
        """
        自分の所有または参加しているスタジオを取得する。

        Args:
            start_page (int|None, optional): 取得するコメントの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するコメントの終了ページ位置。初期値はstart_pageの値です。
            type (Literal["all","owned","curated"], optional): 取得したいスタジオの種類。デフォルトは"all"です。
            sort (Literal["","projecters_count","title"], optional): ソートしたい順。デフォルトは ""です。
            descending (bool, optional): 降順にするか。デフォルトはTrueです。

        Yields:
            Studio: 取得したスタジオ
        """
        add_params:dict[str,str|int|float] = {"descsort":sort} if descending else {"ascsort":sort}
        async for _s in page_api_iterative(
            self.client,f"https://scratch.mit.edu/site-api/galleries/{type}/",
            start_page,end_page,add_params
        ):
            _s:OldAnyObjectPayload[OldStudioPayload]
            yield Studio._create_from_data(_s["pk"],_s["fields"],self,"_update_from_old_data")
    
    async def get_followings_loves(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Project", None]:
        """
        フォロー中のユーザーが好きなプロジェクトを取得する。

        Args:
            limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
            offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。

        Yields:
            Project: 取得したプロジェクト
        """
        async for _p in api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/following/users/loves",
            limit=limit,offset=offset
        ):
            yield Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def get_viewed_projects(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["Project", None]:
        """
        プロジェクトの閲覧履歴を取得する。

        Args:
            limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
            offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。

        Yields:
            Project: 取得したプロジェクト
        """
        async for _p in api_iterative(
            self.client,f"https://api.scratch.mit.edu/users/{self.username}/projects/recentlyviewed",
            limit=limit,offset=offset
        ):
            yield Project._create_from_data(_p["id"],_p,self.client_or_session)

    async def empty_trash(self,password:str) -> int:
        """
        ゴミ箱を空にする

        Args:
            password (str): アカウントのパスワード

        Returns:
            int: 削除されたプロジェクトの数
        """
        r = await self.client.put(
            "https://scratch.mit.edu/site-api/projects/trashed/empty/",
            json={"csrfmiddlewaretoken":"a","password":password}
        )
        return r.json().get("trashed")
    
    async def get_project(self,project_id:int) -> "Project":
        """
        プロジェクトを取得する。

        Args:
            project_id (int): 取得したいプロジェクトのID

        Returns:
            Project: 取得したプロジェクト
        """
        return await Project._create_from_api(project_id,self.session)
    
    async def get_studio(self,studio_id:int) -> "Studio":
        """
        スタジオを取得する。

        Args:
            studio_id (int): 取得したいスタジオのID

        Returns:
            Studio: 取得したスタジオ
        """
        return await Studio._create_from_api(studio_id,self.session)
    
    async def get_user(self,username:str) -> "User":
        """
        ユーザーを取得する。

        Args:
            username (str): 取得したいユーザーの名前

        Returns:
            User: 取得したユーザー
        """
        return await User._create_from_api(username,self.session)
    
    def cloud(
            self,
            project_id:int|str,
            *,
            timeout:aiohttp.ClientWSTimeout|None=None,
            send_timeout:float|None=None
        ) -> ScratchCloud:
        return ScratchCloud(self,project_id,timeout=timeout,send_timeout=send_timeout)
    
def session_login(session_id:str) -> _AwaitableContextManager[Session]:
    """
    セッションIDからアカウントにログインする。

    async with または await でSessionを取得できます。

    Args:
        session_id (str): _description_

    Raises:
        HTTPError: 不明な理由でログインに失敗した。
        ValueError: 無効なセッションID。

    Returns:
        _AwaitableContextManager[Session]: await か async with で取得できるセッション。
    """
    return _AwaitableContextManager(Session._create_from_api(session_id))

async def _login(
        username:str,
        password:str,
        load_status:bool=True,
        *,
        recaptcha_code:str|None=None
    ):
    _client = HTTPClient()
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
    except Forbidden as e:
        await _client.close()
        if type(e) is not Forbidden:
            raise
        raise LoginFailure(e.response) from None
    except:
        await _client.close()
        raise
    set_cookie = response._response.headers.get("Set-Cookie","")
    session_id = split(set_cookie,"scratchsessionsid=\"","\"")
    if not session_id:
        raise LoginFailure(response)
    if load_status:
        return await Session._create_from_api(session_id,_client)
    else:
        return Session(session_id,_client)
    
def login(username:str,password:str,load_status:bool=True,*,recaptcha_code:str|None=None) -> _AwaitableContextManager[Session]:
    """_summary_

    _extended_summary_

    Args:
        username (str): ユーザー名
        password (str): パスワード
        load_status (bool, optional): アカウントのステータスを取得するか。デフォルトはTrueです。
        recaptcha_code (str | None, optional)

    Raises:
        LoginFailure: ログインに失敗した。
        HTTPError: 不明な理由でログインに失敗した。

    Returns:
        _AwaitableContextManager[Session]: await か async with で取得できるセッション
    """
    return _AwaitableContextManager(_login(username,password,load_status,recaptcha_code=recaptcha_code))