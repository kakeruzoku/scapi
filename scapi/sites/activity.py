from __future__ import annotations

import datetime
from enum import Enum
import json
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final, Literal, TypedDict

import bs4

from .base import _BaseSiteAPI
from ..utils.types import (
    WSCloudActivityPayload,
    CloudLogPayload
)
from ..utils.activity_types import (
    ActivityBase,
    ClassAnyActivity,
    ClassBaseActivity
)
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    dt_from_timestamp,
    dt_from_isoformat
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
    from .studio import Studio
    from .user import User
    from .comment import Comment

class CloudActivityPayload(TypedDict):
    method:str
    variable:str
    value:str
    username:str|None
    project_id:int|str
    datetime:datetime.datetime
    cloud:"_BaseCloud|None"

class ActivityType(Enum):
    studio="studio"
    user="user"
    message="message"
    feed="feed"
    classroom="classroom"

class ActivityAction(Enum):
    Unknown="unknown"

class Activity:
    def __init__(
            self,
            type:ActivityType,
            action:ActivityAction=ActivityAction.Unknown,
            *,
            id:int|None=None,
            actor:"User|None"=None,
            target:"Comment|Studio|Project|User|None"=None,
            place:"Studio|Project|User|None"=None,
            datetime:"datetime.datetime|None"=None,
            other:Any=None
        ):
        self.type:ActivityType = type
        self.action:ActivityAction = action
            
        self.id:int|None = id
        self.actor:"User|None" = actor
        self.target:"Comment|Studio|Project|User|None" = target
        self.place:"Studio|Project|User|None" = place
        self.created_at:"datetime.datetime|None" = datetime
        self.other:Any = other

    def _setup_from_json(self,data:ActivityBase,client_or_session:"HTTPClient|Session"):
        from .user import User
        self.actor = User(data["actor_username"],client_or_session)
        self.actor.id = data.get("actor_id")
        self.action = ActivityAction(data["type"])
        self.created_at = dt_from_isoformat(data.get("datetime_created",None))

    @classmethod
    def _create_from_data(cls,data:ClassAnyActivity,client_or_session:"HTTPClient|Session"):
        activity = cls(ActivityType.classroom)
        _actor = data["actor"]
        activity.actor = User._create_from_data(_actor["username"],_actor,client_or_session,User._update_from_old_data)
        #TODO
        return activity



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
    def _create_from_log(cls,payload:CloudLogPayload,id:int|str,client_or_session:"HTTPClient|Session"):
        _value = payload.get("value",None)
        return cls({
            "method":payload.get("verb").removesuffix("_var"),
            "cloud":None,
            "datetime":dt_from_timestamp(payload.get("timestamp")/1000),
            "project_id":id,
            "username":payload.get("user"),
            "value":"" if _value is None else str(_value),
            "variable":payload.get("name")
        },client_or_session)