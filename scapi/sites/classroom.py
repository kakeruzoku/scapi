from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final, Literal, overload
import csv
import io

import aiohttp

from ..utils.types import (
    ClassroomPayload,
    OldAllClassroomPayload,
    OldBaseClassroomPayload,
    OldIdClassroomPayload,
    ClassTokenGeneratePayload,
    ClassStudioCreatePayload,
    OldAnyObjectPayload,
    OldStudioPayload,
    StudentPayload
)
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    UNKNOWN_TYPE,
    _AwaitableContextManager,
    dt_from_isoformat,
    temporary_httpclient,
    page_api_iterative,
    split
)
from ..utils.client import HTTPClient
from ..utils.file import File,_read_file
from ..utils.error import Forbidden,InvalidData,NoDataError

from .base import _BaseSiteAPI
from .studio import Studio
from .user import User
from .activity import Activity

if TYPE_CHECKING:
    from .session import Session

class Classroom(_BaseSiteAPI[int]):
    """
    クラスを表す。

    Attributes:
        id (int): クラスのID
        educator (MAYBE_UNKNOWN[User]): クラスの所有者
        description (MAYBE_UNKNOWN[str]): このクラスについて欄
        status (MAYBE_UNKNOWN[str]): 現在、取り組んでいること
        token (MAYBE_UNKNOWN[str]): クラスのtoken
    """
    def __init__(self,id:int,client_or_session:"HTTPClient|Session|None"=None,*,token:str|None=None):
        super().__init__(client_or_session)
        self.id:Final[int] = id

        self.title:MAYBE_UNKNOWN[str] = UNKNOWN
        self._started_at:MAYBE_UNKNOWN[str] = UNKNOWN
        self.educator:MAYBE_UNKNOWN[User] = UNKNOWN
        self.closed:MAYBE_UNKNOWN[bool] = UNKNOWN

        self.token:MAYBE_UNKNOWN[str] = token or UNKNOWN
        self.description:MAYBE_UNKNOWN[str] = UNKNOWN
        self.status:MAYBE_UNKNOWN[str] = UNKNOWN

        self.studio_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.student_count:MAYBE_UNKNOWN[int] = UNKNOWN
        self.unread_alert_count:MAYBE_UNKNOWN[int] = UNKNOWN

    async def update(self) -> None:
        response = await self.client.get(f"https://api.scratch.mit.edu/classrooms/{self.id}")
        self._update_from_data(response.json())

    @property
    def started_at(self) -> datetime.datetime|UNKNOWN_TYPE:
        """
        クラスが開始した時間。

        Returns:
            datetime.datetime|UNKNOWN_TYPE:
        """
        return dt_from_isoformat(self._started_at)

    def _update_from_data(self, data:ClassroomPayload):
        self.closed = False #closeしてたらapiから取得できない
        self._update_to_attributes(
            title=data.get("title"),
            description=data.get("description"),
            status=data.get("status"),
            _started_at=data.get("data_start"),
        )

        _educator = data.get("educator")
        if _educator:
            if self.educator is UNKNOWN:
                self.educator = User(_educator["username"])
            self.educator._update_from_data(_educator)

    def _update_from_old_data(self, data:OldBaseClassroomPayload):
        self._update_to_attributes(
            title=data.get("title"),
            _started_at=data.get("datetime_created"),
            token=data.get("token"),
            studio_count=data.get("gallery_count"),
            student_count=data.get("student_count"),
            unread_alert_count=data.get("unread_alert_count")
        )
        if self.session is not None:
            self.educator = self.educator or self.session.user

    def _update_from_all_mystuff_data(self,data:OldAllClassroomPayload):
        self.closed = data.get("visibility") == "closed"
        self._update_from_old_data(data)

    def _update_from_id_mystuff_data(self,data:OldIdClassroomPayload):
        self._update_to_attributes(
            description=data.get("description"),
            status=data.get("status"),
        )
        self._update_from_old_data(data)

    async def edit(
            self,
            title:str|None=None,
            description:str|None=None,
            status:str|None=None,
            open:bool|None=None
        ):
        """
        クラスを編集する。

        Args:
            title (str | None, optional): クラスのタイトル
            description (str | None, optional): このクラスについて
            status (str | None, optional): 現在、取り組んでいること
            open (bool | None, optional): クラスを開けるか
        """
        data = {}
        self.require_session()
        if title is not None: data["title"] = title
        if description is not None: data["description"] = description
        if status is not None: data["status"] = status
        if open is not None: data["visibility"] = "visible" if open else "closed"
        response = await self.client.put(f"https://scratch.mit.edu/site-api/classrooms/all/{self.id}/",json=data)
        self._update_from_id_mystuff_data(response.json())

    async def set_icon(self,icon:File|bytes):
        """
        アイコンを変更する。

        Args:
            icon (file.File | bytes): アイコンのデータ
        """
        self.require_session()
        async with _read_file(icon) as f:
            self.require_session()
            await self.client.post(
                f"https://scratch.mit.edu/site-api/classrooms/all/{self.id}/",
                data=aiohttp.FormData({"file":f})
            )

    async def create_class_studio(self,title:str,description:str|None=None) -> Studio:
        """
        クラスのスタジオを作成する

        Args:
            title (str): スタジオのタイトル
            description (str | None, optional): スタジオの説明欄

        Returns:
            Studio: 作成されたスタジオ
        """
        self.require_session()
        response = await self.client.post(
            "https://scratch.mit.edu/classes/create_classroom_gallery/",
            json={
                "classroom_id":str(self.id),
                "classroom_token":self.token,
                "title":title,
                "description":description or "",
                "csrfmiddlewaretoken":"a"
            }
        )
        data:ClassStudioCreatePayload = response.json()[0]
        if not data["msg"]:
            raise Forbidden(response,data.get("msg"))
        studio = Studio(data["gallery_id"],self.client_or_session)
        studio.title = data.get("gallery_title")
        return studio
    
    async def get_class_studios(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator[Studio]:
        """
        クラスのスタジオを取得する。

        Args:
            start_page (int|None, optional): 取得するスタジオの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するスタジオの終了ページ位置。初期値はstart_pageの値です。

        Yields:
            Studio: 取得したスタジオ
        """
        self.require_session()
        async for _s in page_api_iterative(
            self.client,f"https://scratch.mit.edu/site-api/classrooms/studios/{self.id}/",
            start_page,end_page
        ):
            _s:OldAnyObjectPayload[OldStudioPayload]
            yield Studio._create_from_data(_s["pk"],_s["fields"],self.client_or_session,Studio._update_from_old_data)

    async def get_class_students(self,start_page:int|None=None,end_page:int|None=None) -> AsyncGenerator[User]:
        """
        クラスの生徒を取得する。

        Args:
            start_page (int|None, optional): 取得するユーザーの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するユーザーの終了ページ位置。初期値はstart_pageの値です。

        Yields:
            User: 取得したユーザー
        """
        self.require_session()
        async for _u in page_api_iterative(
            self.client,f"https://scratch.mit.edu/site-api/classrooms/students/{self.id}/",
            start_page,end_page
        ):
            _u:OldAnyObjectPayload[StudentPayload]
            yield User._create_from_data(_u["fields"]["user"]["username"],_u["fields"],self.client_or_session,User._update_from_student_data)

    async def get_class_activity(
            self,
            start_page:int|None=None,
            end_page:int|None=None,
            student:str|User|None=None,
            sort:Literal["","username"]="",
            descending:bool=True
        ) -> AsyncGenerator[Activity]:
        self.require_session()
        add_params:dict[str,str|int|float] = {"descsort":sort} if descending else {"ascsort":sort}
        student = student.username if isinstance(student,User) else (student or "all")
        async for _a in page_api_iterative(
            self.client,f"https://scratch.mit.edu/site-api/classrooms/activity/{self.id}/{student}/",
            start_page,end_page,add_params
        ):
            yield Activity._create_from_class(_a,self.client_or_session)

    @overload
    async def create_student_account(
        self,username:str,*,load_status:bool=True
    ) -> "Session":
        ...
    
    @overload
    async def create_student_account(
        self,username:str,password:str,birth_day:datetime.date,gender:str,country:str,
        *,load_status:bool=True
    ) -> "Session":
        ...

    async def create_student_account(
        self,username:str,
        password:str|None=None,
        birth_day:datetime.date|None=None,
        gender:str|None=None,
        country:str|None=None,
        *,
        load_status:bool=True
    ) -> "Session":
        """
        tokenから生徒アカウントを作成する。
        ユーザー名のみを指定して作成することもできます。

        Args:
            username (str): アカウントのユーザー名
            password (str | None, optional): アカウントのパスワード
            birth_day (datetime.date | None, optional): 登録したい誕生日
            gender (str | None, optional): 登録したい性別
            country (str | None, optional): 登録したい国
            load_status (bool, optional): アカウントのステータスを取得するか。デフォルトはTrueです。

        Returns:
            Session: 作成されたアカウント
        """
        if self.token is None:
            raise NoDataError(self)
        data = aiohttp.FormData({
            "classroom_id":self.id,
            "classroom_token": self.token,
            "username": username,
            "is_robot": False
        })
        if password and birth_day and gender and country:
            data.add_fields({
                "password": password,
                "birth_month": birth_day.month,
                "birth_year": birth_day.year,
                "gender": gender,
                "country": country,
            })
        response = await self.client.post(
            "https://scratch.mit.edu/classes/register_new_student/",data=data,
            cookies={"scratchcsrftoken": 'a'}
        )
        set_cookie = response._response.headers.get("Set-Cookie","")
        session_id = split(set_cookie,"scratchsessionsid=\"","\"")
        if not session_id:
            raise InvalidData(response)
        if load_status:
            return await Session._create_from_api(session_id)
        else:
            return Session(session_id)
        
    async def create_student_accounts(self,data:dict[str,str]):
        """
        教師アカウントから生徒アカウントを作成します。
        同時に40アカウントまで作成できます。

        Args:
            data (dict[str,str]): 作成したいアカウントのユーザー名とパスワードのペア
        """
        self.require_session()
        temp_stream = io.StringIO(newline="")
        csv.writer(temp_stream).writerows(data.items())
        temp_stream.seek(0)
        csv_data = temp_stream.getvalue()
        form_data = aiohttp.FormData(default_to_multipart=True)
        form_data.add_field("csrfmiddlewaretoken","a")
        form_data.add_field("csv_file",csv_data.encode(),content_type="text/plain")
        form_data.add_field("piiConfirm","on")

        await self.client.post(f"https://scratch.mit.edu/classes/{self.id}/student_upload/",data=form_data)


    async def get_token(self,generate:bool=True) -> tuple[str,datetime.datetime]:
        """
        生徒アカウントを作成するためのトークンを取得する。
        新たにトークンを生成した場合、過去のトークンは無効になります。

        Args:
            generate (bool, optional): 新たにトークン生成するか。デフォルトはTrueです。

        Returns:
            tuple[str,datetime.datetime]: 取得したトークンと、そのトークンの有効期限
        """
        self.require_session()
        if generate:
            response = await self.client.post(f"https://scratch.mit.edu/site-api/classrooms/generate_registration_link/{self.id}/")
        else:
            response = await self.client.get(f"https://scratch.mit.edu/site-api/classrooms/generate_registration_link/{self.id}/")
        data:ClassTokenGeneratePayload = response.json()
        if not data["success"]:
            raise Forbidden(response,data.get("error"))
        
        self.token = split(data.get("reg_link"),"/signup/","/",True)
        return self.token,dt_from_isoformat(data.get("expires_at"))

def get_class(class_id:int,*,_client:HTTPClient|None=None) -> _AwaitableContextManager[Classroom]:
    """
    クラスを取得する。

    Args:
        class_id (int): 取得したいクラスのID

    Returns:
        _AwaitableContextManager[Classroom]: await か async with で取得できるクラス
    """
    return _AwaitableContextManager(Classroom._create_from_api(class_id,_client))

async def _get_class_from_token(token:str,client_or_session:"HTTPClient|Session|None"=None) -> Classroom:
    async with temporary_httpclient(client_or_session) as client:
        response = await client.get(f"https://api.scratch.mit.edu/classtoken/{token}")
        data:ClassroomPayload = response.json()
        return Classroom._create_from_data(data["id"],data,client_or_session,token=token)

def get_class_from_token(token:str,*,_client:HTTPClient|None=None) -> _AwaitableContextManager[Classroom]:
    """
    クラストークンからクラスを取得する。

    Args:
        token (str): 取得したいクラスのtoken

    Returns:
        _AwaitableContextManager[Classroom]: await か async with で取得できるクラス
    """
    return _AwaitableContextManager(_get_class_from_token(token,_client))