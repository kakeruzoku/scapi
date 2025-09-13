from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final, Literal

from ..utils.types import (
    ClassroomPayload,
    OldAllClassroomPayload,
    OldBaseClassroomPayload,
    OldIdClassroomPayload
)
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    UNKNOWN_TYPE,
    get_client_and_session,
    _AwaitableContextManager,
    dt_from_isoformat,
    temporary_httpclient
)
from ..utils.client import HTTPClient

from .base import _BaseSiteAPI
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
        self._ended_at:MAYBE_UNKNOWN[str|None] = UNKNOWN
        self.educator:MAYBE_UNKNOWN[User] = UNKNOWN

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
    
    @property
    def ended_at(self) -> datetime.datetime|UNKNOWN_TYPE|None:
        """
        クラスが終了した時間。クラスが終了すると、APIから取得できなくなるためこの値は常にNoneになります。

        Returns:
            datetime.datetime|UNKNOWN_TYPE:
        """
        return dt_from_isoformat(self._ended_at)

    def _update_from_data(self, data:ClassroomPayload):
        self._update_to_attributes(
            title=data.get("title"),
            description=data.get("description"),
            status=data.get("status"),
            _started_at=data.get("data_start"),
            _ended_at=data.get("data_end"),
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
        self._update_from_old_data(data)

    def _update_from_id_mystuff_data(self,data:OldIdClassroomPayload):
        self._update_to_attributes(
            description=data.get("description"),
            status=data.get("status"),
        )
        self._update_from_old_data(data)

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