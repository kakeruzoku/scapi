from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final, Literal

import aiohttp

from ..utils.types import (
    ClassroomPayload,
    OldAllClassroomPayload,
    OldBaseClassroomPayload,
    OldIdClassroomPayload,
    ClassTokenGeneratePayload,
    ClassStudioCreatePayload,
    OldAnyObjectPayload,
    OldStudioPayload
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
from ..utils.error import Forbidden

from .base import _BaseSiteAPI
from .studio import Studio
from .user import User

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
    
    async def get_class_studios(
            self,
            start_page:int|None=None,
            end_page:int|None=None,
        ) -> AsyncGenerator[Studio]:
        """
        クラスのスタジオを取得する。

        Args:
            start_page (int|None, optional): 取得するスタジオの開始ページ位置。初期値は1です。
            end_page (int|None, optional): 取得するスタジオの終了ページ位置。初期値はstart_pageの値です。

        Yields:
            Studio: 取得したスタジオ
        """
        async for _s in page_api_iterative(
            self.client,f"https://scratch.mit.edu/site-api/classrooms/studios/{self.id}/",
            start_page,end_page
        ):
            _s:OldAnyObjectPayload[OldStudioPayload]
            yield Studio._create_from_data(_s["pk"],_s["fields"],self.client_or_session,Studio._update_from_old_data)

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
        _AwaitableContextManager[Project]: await か async with で取得できるクラス
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
        _AwaitableContextManager[Project]: await か async with で取得できるクラス
    """
    return _AwaitableContextManager(_get_class_from_token(token,_client))