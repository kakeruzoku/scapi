from __future__ import annotations

import datetime
import json
from typing import TYPE_CHECKING, AsyncGenerator, Final, Literal, TypedDict

import bs4

from .base import _BaseSiteAPI
from ..utils.types import (
    WSCloudActivityPayload
)
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
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
    cloud:"_BaseCloud"


class CloudActivity(_BaseSiteAPI):
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
        self.cloud:"_BaseCloud" = payload.get("cloud")

    async def get_user(self) -> "User":
        from .user import User
        if self.username is UNKNOWN:
            raise NoDataError(self)
        return await User._create_from_api(self.username)
    
    async def get_project(self) -> "Project":
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