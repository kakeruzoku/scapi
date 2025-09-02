from __future__ import annotations

import datetime
import json
from typing import TYPE_CHECKING, AsyncGenerator, Final, Literal, TypedDict

import bs4

from .base import _BaseSiteAPI
from ..utils.types import (
    WSCloudActivityPayload,
    CloudLogPayload
)
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    dt_from_timestamp
)
from ..utils.error import (
    NoDataError,
)

if TYPE_CHECKING:
    from .session import Session
    from ..utils.client import HTTPClient
    from ..event.cloud import _BaseCloud
    from .user import User
    from .project import Project

class CloudActivityPayload(TypedDict):
    method:str
    variable:str
    value:str
    username:str|None
    project_id:int|str
    datetime:datetime.datetime
    cloud:"_BaseCloud|None"


class CloudActivity(_BaseSiteAPI):
    """
    クラウド変数の操作ログを表すクラス。

    Attributes:
        method (str): 操作の種類
        variable (str): 操作された変数の名前
        value (str): 新しい値
        username (MAYBE_UNKNOWN[str]): 利用できる場合、変更したユーザーのユーザー名
        project_id (int|str): プロジェクトID
        datetime (datetime.datetime) ログが実行された時間
        cloud (_BaseCloud|None) このログに関連付けられているクラウド変数クラス
    """
    def __repr__(self):
        return f"<CloudActivity method:{self.method} id:{self.project_id} user:{self.username} variable:{self.variable} value:{self.value}>"

    def __init__(self,payload:CloudActivityPayload,client_or_session:"HTTPClient|Session|None"=None):
        super().__init__(client_or_session)

        self.method:str = payload.get("method")
        self.variable:str = payload.get("variable")
        self.value:str = payload.get("value")

        self.username:MAYBE_UNKNOWN[str] = payload.get("username") or UNKNOWN
        self.project_id:int|str = payload.get("project_id")
        self.datetime:datetime.datetime = payload.get("datetime")
        self.cloud:"_BaseCloud|None" = payload.get("cloud")

    async def get_user(self) -> "User":
        """
        ユーザー名からユーザーを取得する。

        Raises:
            NoDataError: ユーザー名の情報がない。

        Returns:
            User:
        """
        from .user import User
        if self.username is UNKNOWN:
            raise NoDataError(self)
        return await User._create_from_api(self.username)
    
    async def get_project(self) -> "Project":
        """
        プロジェクトIDからプロジェクトを取得する。

        Raises:
            ValueError: プロジェクトIDがintに変換できない。

        Returns:
            Project:
        """
        from .project import Project
        if isinstance(self.project_id,str) and not self.project_id.isdecimal():
            raise ValueError("Invalid project ID")
        return await Project._create_from_api(int(self.project_id))
    
    @classmethod
    def _create_from_ws(cls,payload:WSCloudActivityPayload,cloud:"_BaseCloud") -> "CloudActivity":
        return cls({
            "method":"set",
            "cloud":cloud,
            "datetime":datetime.datetime.now(),
            "project_id":cloud.project_id,
            "username":None,
            "value":payload.get("value"),
            "variable":payload.get("name")
        },cloud.session or cloud.client)
    
    @classmethod
    def _create_from_log(cls,payload:CloudLogPayload,project:"Project"):
        _value = payload.get("value",None)
        return cls({
            "method":payload.get("verb").removesuffix("_var"),
            "cloud":None,
            "datetime":dt_from_timestamp(payload.get("timestamp")/1000),
            "project_id":project.id,
            "username":payload.get("user"),
            "value":"" if _value is None else str(_value),
            "variable":payload.get("name")
        },project.client_or_session)