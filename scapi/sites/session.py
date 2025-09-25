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
    OldStudioPayload,
    ClassCreatedPayload,
    OldAllClassroomPayload,
    OldIdClassroomPayload,
    StudioCreatedPayload,
    MessageCountPayload,
    ScratcherInvitePayload,
    NoElementsPayload,
    AnySuccessPayload,
    search_mode,
    explore_query
)
from ..utils.client import HTTPClient
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    UNKNOWN_TYPE,
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
from ..utils.config import _config
from ..utils.file import File,_file
from ..event.cloud import ScratchCloud
from .base import _BaseSiteAPI

from .classroom import Classroom,_get_class_from_token
from .project import Project, search_projects, explore_projects
from .studio import Studio, search_studios, explore_studios
from .user import User
from .forum import ForumCategory,get_forum_categories,ForumTopic,ForumPost

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
        birthday (datetime.date|None): アカウントに登録された誕生日。日付は常に`1`です
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
        birth_year = _user.get("birthYear")
        birth_month = _user.get("birthMonth")
        if birth_year and birth_month:
            self.birthday = datetime.date(birth_year,birth_month,1)
        else:
            self.birthday = None
        self.gender = _user.get("gender")
        self.classroom_id = _user.get("classroomId",None)

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

    async def change_country(self,country:str):
        """
        アカウントに表示される国を変更する

        Args:
            country (str): 変更先の国名
        """
        await self.client.post(
            "https://scratch.mit.edu/accounts/settings/",
            data=aiohttp.FormData({"country":country})
        )

    async def change_password(self,old_password:str|None,new_password:str,is_reset:bool=False):
        """
        アカウントのパスワードを変更します。

        Args:
            old_password (str | None): 現在のパスワード(通常のパスワード変更の場合はstrのみ使用できます。)
            new_password (str): 新しいパスワード
            is_reset (bool, optional): 生徒アカウントのパスワードリセットの場合、Trueにしてください。
        """
        if (not _config.bypass_checking) and self.status and self.status.must_reset_password:
            is_reset = True
        if is_reset:
            req_url = "https://scratch.mit.edu/classes/student_password_reset/"
            data = aiohttp.FormData({
                "csrfmiddlewaretoken":"a",
                "new_password1":new_password,
                "new_password2":new_password
            })
        else:
            if old_password is None:
                raise ValueError()
            req_url = "https://scratch.mit.edu/accounts/password_change/"
            data = aiohttp.FormData({
                "csrfmiddlewaretoken":"a",
                "old_password": old_password,
                "new_password1":new_password,
                "new_password2":new_password
            })
        response = await self.client.post(req_url,data=data,check=False)
        if str(response._response.url) == req_url:
            raise Forbidden(response)
        response._check()

    async def change_email(self,new_email:str,password:str):
        """
        アカウントに登録されているメールアドレスを変更する。

        Args:
            new_email (str): 新たなメールアドレス
            password (str): パスワード
        """
        await self.client.post(
            "https://scratch.mit.edu/accounts/email_change/",
            data=aiohttp.FormData({
                "email_address": new_email,
                "password": password
            })
        )

    async def change_subscription(self,*,activities:bool=False,teacher_tips:bool=False):
        """
        登録しているメールアドレスへの配信を設定する。

        Args:
            activities (bool, optional): 家庭でScratchを使う活動のアイデアを受け取るか。デフォルトはFalseです。
            teacher_tips (bool, optional): Scratchを教育現場向け設定にするためのプロダクトアップデートを受け取るか。デフォルトはFalseです。
        """
        formdata = aiohttp.FormData({"csrfmiddlewaretoken":"a"})
        if activities:
            formdata.add_field("activities","on")
        if teacher_tips:
            formdata.add_field("teacher_tips","on")
        await self.client.post(
            "https://scratch.mit.edu/accounts/settings/update_subscription/",
            data=formdata
        )

    async def register_info(self,password:str,birth_day:datetime.date,gender:str,country:str):
        """
        新しい生徒アカウントに個人情報を登録する。

        Args:
            password (str): 新しいパスワード
            birth_day (datetime.date): 誕生日
            gender (str): 性別
            country (str): 国
        """
        data = aiohttp.FormData({
            "birth_month":str(birth_day.month),
            "birth_year":str(birth_day.year),
            "gender":gender,
            "country":country,
            "is_robot":"false",
            "password":password
        })
        await self.client.post("https://scratch.mit.edu/classes/student_update_registration/",data=data)
    
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
    
    async def create_studio(self) -> Studio:
        """
        スタジオを作成する

        Returns:
            Studio: 作成されたスタジオ
        """
        response = await self.client.post("https://scratch.mit.edu/studios/create/")
        data:StudioCreatedPayload = response.json()
        return Studio(int(split(data.get("redirect"),"/studios/","/",True)),self.session)
    
    async def create_class(
            self,
            title:str,
            description:str|None=None,
            status:str|None=None
        ) -> Classroom:
        """
        クラスを作成する。

        クラスを作成するには教師アカウントが必要です。
        6カ月に10クラスまで作成できます。

        Args:
            title (str): 作成したいクラスの名前
            description (str | None, optional): このクラスについて欄
            status (str | None, optional): 現在、取り組んでいること欄

        Returns:
            Classroom: 作成されたクラス
        """
        response = await self.client.post(
            "https://scratch.mit.edu/classes/create_classroom/",
            json={
                "title":title,
                "description":description or "",
                "status":status or "",
                "is_robot":False,
                "csrfmiddlewaretoken":"a"
            }
        )
        data:ClassCreatedPayload = response.json()[0]
        if not data["success"]:
            raise 
        classroom = Classroom(data["id"],self.session)
        classroom.title = data.get("title")
        classroom.description = description or ""
        classroom.status = status or ""
        return classroom
    
    async def clear_message(self):
        await self.client.post("https://scratch.mit.edu/site-api/messages/messages-clear/")

    async def get_message_count(self) -> int:
        """
        アカウントのメッセージ数を取得する。

        Returns:
            int:
        """
        response = await self.client.get("https://api.scratch.mit.edu/users/fas/messages/count")
        data:MessageCountPayload = response.json()
        return data.get("count",0)
    
    async def get_invite_status(self) -> ScratcherInvitePayload|None:
        """
        Scratcherへの招待への詳細データ

        Returns:
            ScratcherInvitePayload|None: 招待がある場合、Scratchからの生データ
        """
        response = await self.client.get(f"https://api.scratch.mit.edu/users/{self.username}/invites")
        data:ScratcherInvitePayload|None = response.json() # NoElementsPayloadのほうが適切
        return data or None
    
    async def become_scratcher(self):
        """
        Scratcherに昇格する。
        """
        await self.client.get(f"https://scratch.mit.edu/users/{self.username}/promote-to-scratcher/")
    
    async def get_my_classroom(self) -> Classroom|None|UNKNOWN_TYPE:
        """
        生徒アカウントの場合、参加しているクラスを取得する。

        Returns:
            Classroom|None|UNKNOWN_TYPE:
        """
        if self.status is UNKNOWN:
            return UNKNOWN
        if self.status.classroom_id is None:
            return
        return await Classroom._create_from_api(self.status.classroom_id,self)
    
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
            start_page (int|None, optional): 取得するプロジェクトの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するプロジェクトの終了ページ位置。初期値はstart_pageの値です。
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
            yield Project._create_from_data(_p["pk"],_p["fields"],self,Project._update_from_old_data)

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
            start_page (int|None, optional): 取得するスタジオの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するスタジオの終了ページ位置。初期値はstart_pageの値です。
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
            yield Studio._create_from_data(_s["pk"],_s["fields"],self,Studio._update_from_old_data)

    async def get_mystuff_classes(
            self,
            start_page:int|None=None,
            end_page:int|None=None,
            type:Literal["all","closed"]="all",
            sort:Literal["","student_count","title"]="",
            descending:bool=True
        ) -> AsyncGenerator[Classroom]:
        """
        自分の所有しているクラスを取得する。

        Args:
            start_page (int|None, optional): 取得するクラスの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するクラスの終了ページ位置。初期値はstart_pageの値です。
            type (Literal["all","closed"], optional): 取得したいクラスの種類。デフォルトは"all"です。
            sort (Literal["","student_count","title"], optional): ソートしたい順。デフォルトは ""です。
            descending (bool, optional): 降順にするか。デフォルトはTrueです。

        Yields:
            Studio: 取得したスタジオ
        """
        add_params:dict[str,str|int|float] = {"descsort":sort} if descending else {"ascsort":sort}
        async for _s in page_api_iterative(
            self.client,f"https://scratch.mit.edu/site-api/classrooms/{type}/",
            start_page,end_page,add_params
        ):
            _s:OldAnyObjectPayload[OldAllClassroomPayload]
            yield Classroom._create_from_data(_s["pk"],_s["fields"],self,Classroom._update_from_all_mystuff_data)

    async def get_mystuff_class(self,id:int) -> Classroom:
        """
        所有しているクラスの情報を取得する。

        Args:
            id (int): 取得したいクラスのID

        Returns:
            Classroom:
        """
        response = await self.client.get(f"https://scratch.mit.edu/site-api/classrooms/all/{id}/")
        data:OldIdClassroomPayload = response.json()
        return Classroom._create_from_data(id,data,self,Classroom._update_from_id_mystuff_data)
    
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
    
    async def check_password(self,password:str):
        """
        アカウントのパスワードを確認する

        Args:
            password (str): アカウントのパスワード

        Returns:
            bool: パスワードが正しいかどうか
        """
        response = await self.client.post(
            "https://scratch.mit.edu/accounts/check_password/",
            data=aiohttp.FormData({
                "csrfmiddlewaretoken":"a",
                "password":password
            })
        )
        data:AnySuccessPayload = response.json()
        return bool(data.get("success"))
    
    async def get_project(self,project_id:int) -> "Project":
        """
        プロジェクトを取得する。

        Args:
            project_id (int): 取得したいプロジェクトのID

        Returns:
            Project: 取得したプロジェクト
        """
        return await Project._create_from_api(project_id,self)
    
    async def get_studio(self,studio_id:int) -> "Studio":
        """
        スタジオを取得する。

        Args:
            studio_id (int): 取得したいスタジオのID

        Returns:
            Studio: 取得したスタジオ
        """
        return await Studio._create_from_api(studio_id,self)
    
    async def get_user(self,username:str) -> "User":
        """
        ユーザーを取得する。

        Args:
            username (str): 取得したいユーザーの名前

        Returns:
            User: 取得したユーザー
        """
        return await User._create_from_api(username,self)
    
    async def get_classroom(self,class_id:int) -> Classroom:
        """
        クラスを取得する。

        Args:
            class_id (int): 取得したいクラスのID

        Returns:
            Classroom:
        """
        return await Classroom._create_from_api(class_id,self)
    
    async def get_classroom_from_token(self,token:str) -> Classroom:
        """
        classtokenからクラスを取得する。

        Args:
            token (str): 取得したいクラスのtoken

        Returns:
            Classroom:
        """
        return await _get_class_from_token(token,self)
    
    async def get_forum_categories(self) -> dict[str, list[ForumCategory]]:
        """
        フォーラムのカテゴリー一覧を取得する。

        Returns:
            dict[str, list[ForumCategory]]: ボックスの名前と、そこに属しているカテゴリーのペア
        """
        return await get_forum_categories(self)
    
    async def get_forum_category(self,category_id:int) -> ForumCategory:
        """
        フォーラムカテゴリーを取得する

        Args:
            category_id (int): 取得したいカテゴリーのID

        Returns:
            ForumCategory:
        """
        return await ForumCategory._create_from_api(category_id,self)
    
    async def get_forum_topic(self,topic_id:int) -> ForumTopic:
        """
        フォーラムトピックを取得する

        Args:
            topic_id (int): 取得したいトピックのID

        Returns:
            ForumTopic:
        """
        return await ForumTopic._create_from_api(topic_id,self)
    
    async def get_forum_post(self,post_id:int) -> ForumPost:
        """
        フォーラムの投稿を取得する

        Args:
            post_id (int): 取得したい投稿のID

        Returns:
            ForumPost:
        """
        return await ForumPost._create_from_api(post_id,self)
    
    def explore_projects(
            self,
            query: explore_query = "*",
            mode: search_mode = "trending",
            language: str = "en",
            limit: int | None = None,
            offset: int | None = None,
        ) -> AsyncGenerator[Project, None]:
        """
        プロジェクトの傾向を取得する。
        この関数は ``async for`` から使用してください。

        Args:
            query (explore_query, optional): 取得するする種類。デフォルトは"*"(all)です。
            mode (Literal["trending","popular"], optional): 取得するモード。デフォルトは"trending"です。
            language (str, optional): 取得する言語。デフォルトは"en"です。
            limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
            offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。

        Returns:
            AsyncGenerator[Project, None]:
        """
        return explore_projects(self.client,query,mode,language,limit,offset)
    
    def search_projects(
            self,
            query: str,
            mode: search_mode = "trending",
            language: str = "en",
            limit: int | None = None,
            offset: int | None = None,
        ) -> AsyncGenerator[Project, None]:
        """
        プロジェクトを検索する
        この関数は ``async for`` から使用してください。

        Args:
            query (str): 検索したい内容
            mode (Literal["trending","popular"], optional): 取得するモード。デフォルトは"trending"です。
            language (str, optional): 取得する言語。デフォルトは"en"です。
            limit (int|None, optional): 取得するプロジェクトの数。初期値は40です。
            offset (int|None, optional): 取得するプロジェクトの開始位置。初期値は0です。

        Returns:
            AsyncGenerator[Project, None]:
        """
        return search_projects(self.client,query,mode,language,limit,offset)
    
    def explore_studios(
            self,
            query: explore_query = "*",
            mode: search_mode = "trending",
            language: str = "en",
            limit: int | None = None,
            offset: int | None = None,
        ) -> AsyncGenerator[Studio, None]:
        """
        スタジオの傾向を取得する
        この関数は ``async for`` から使用してください。

        Args:
            query (explore_query, optional): 取得するする種類。デフォルトは"*"(all)です。
            mode (Literal["trending","popular"], optional): 取得するモード。デフォルトは"trending"です。
            language (str, optional): 取得する言語。デフォルトは"en"です。
            limit (int|None, optional): 取得するスタジオの数。初期値は40です。
            offset (int|None, optional): 取得するスタジオの開始位置。初期値は0です。

        Returns:
            AsyncGenerator[Studio, None]:
        """
        return explore_studios(self.client,query,mode,language,limit,offset)
    
    def search_studios(
            self,
            query: str,
            mode: search_mode = "trending",
            language: str = "en",
            limit: int | None = None,
            offset: int | None = None,
        ) -> AsyncGenerator[Studio, None]:
        """
        スタジオを検索する
        この関数は ``async for`` から使用してください。

        Args:
            query (str): 検索したい内容
            mode (Literal["trending","popular"], optional): 取得するモード。デフォルトは"trending"です。
            language (str, optional): 取得する言語。デフォルトは"en"です。
            limit (int|None, optional): 取得するスタジオの数。初期値は40です。
            offset (int|None, optional): 取得するスタジオの開始位置。初期値は0です。

        Returns:
            AsyncGenerator[Studio, None]:
        """
        return search_studios(self.client,query,mode,language,limit,offset)

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
    """
    Scratchにログインする。

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