from __future__ import annotations

import datetime
from enum import Enum
import json
from typing import TYPE_CHECKING, Any, AsyncGenerator, Final, Literal, TypedDict

import bs4

from .base import _BaseSiteAPI
from ..utils.types import (
    WSCloudActivityPayload,
    CloudLogPayload,
    OldUserPayload
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
    from .comment import Comment

def _import():
    global User,Project,Studio,Comment
    from .user import User
    from .project import Project
    from .studio import Studio
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

    #studio
    StudioFollow="studio_follow"
    StudioAddProject="studio_add_project"
    StudioRemoveProject="studio_remove_project"
    StudioBecomeCurator="studio_become_curetor" #なった人がactor それを実行した人がtarget
    StudioBecomeManager="studio_become_manager"
    StudioBecomeHost="studio_become_host"
    StudioUpdate="studio_update"

    #project
    ProjectLove="project_love"
    ProjectFavorite="project_favorite"
    ProjectShare="project_share"
    ProjectRemix="project_remix"

    #user
    UserFollow="user_follow"
    UserEditProfile="UserEditProfile"

    #other
    Comment="comment"

class Activity:
    def __str__(self) -> str:
        return f"<Acticity type:{self.type} action:{self.action}>"

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
        _import()
        self.actor = User(data["actor_username"],client_or_session)
        self.actor.id = data.get("actor_id")
        self.action = ActivityAction(data["type"])
        self.created_at = dt_from_isoformat(data.get("datetime_created",None))

    @staticmethod
    def _load_user(data:OldUserPayload,client_or_session:"HTTPClient|Session"):
        return User._create_from_data(data["username"],data,client_or_session,User._update_from_old_data)

    @classmethod
    def _create_from_class(cls,data:ClassAnyActivity,client_or_session:"HTTPClient|Session"):
        _import()
        activity = cls(ActivityType.classroom)
        _actor = data["actor"]
        activity.actor = User._create_from_data(_actor["username"],_actor,client_or_session,User._update_from_old_data)
        activity.created_at = dt_from_isoformat(data["datetime_created"])
        match data["type"]:
            case 0:
                activity.action = ActivityAction.UserFollow
                activity.place = activity.target = cls._load_user(data["followed_user"],client_or_session)
            case 1:
                activity.action = ActivityAction.StudioFollow
                activity.place = activity.target = Studio(data["gallery"],client_or_session)
                activity.place.title = data["title"]
            case 2:
                activity.action = ActivityAction.ProjectLove
                activity.place = activity.target = Project(data["project"],client_or_session)
                activity.place.author = cls._load_user(data["recipient"],client_or_session)
                activity.place.title = data["title"]
            case 3:
                activity.action = ActivityAction.ProjectFavorite
                activity.place = activity.target = Project(data["project"],client_or_session)
                activity.place.author = cls._load_user(data["project_creator"],client_or_session)
                activity.place.title = data["project_title"]
            case 7:
                activity.action = ActivityAction.StudioAddProject
                activity.place = Studio(data["gallery"],client_or_session)
                activity.place.title = data["gallery_title"]
                activity.target = Project(data["project"],client_or_session)
                activity.target.title = data["project_title"]
                activity.target.author = cls._load_user(data["recipient"],client_or_session)
            case 10:
                activity.action = ActivityAction.ProjectShare
                activity.place = activity.target = Project(data["project"],client_or_session)
                activity.place.title = data["title"]
                activity.place.author = activity.actor
                activity.other = data["is_reshare"]
            case 11:
                activity.action = ActivityAction.ProjectRemix
                activity.place = Project(data["project"],client_or_session)
                activity.place.title = data["title"]
                activity.place.author = activity.actor
                activity.target = Project(data["parent"],client_or_session)
                activity.target.title = data["parent_title"]
                activity.target.author = cls._load_user(data["recipient"],client_or_session)
            case 13:
                activity.action = ActivityAction.StudioBecomeHost
                activity.place = activity.target = Studio(data["gallery"],client_or_session)
            case 15:
                activity.action = ActivityAction.StudioUpdate
                activity.place = activity.target = Studio(data["gallery"],client_or_session)
                activity.place.title = data["title"]
            case 19:
                activity.action = ActivityAction.StudioRemoveProject
                activity.place = Studio(data["gallery"],client_or_session)
                activity.place.title = data["gallery_title"]
                activity.target = Project(data["project"],client_or_session)
                activity.target.title = data["project_title"]
                activity.target.author = cls._load_user(data["recipient"],client_or_session)
            case 22:
                activity.action = ActivityAction.StudioBecomeManager
                activity.place = Studio(data["gallery"],client_or_session)
                activity.place.title = data["gallery_title"]
                if data["recipient"] is None:
                    activity.target = activity.actor
                else:
                    activity.target = cls._load_user(data["recipient"],client_or_session)
            case 25:
                activity.action = ActivityAction.UserEditProfile
                activity.place = activity.target = activity.actor
                activity.other = data["changed_fields"]
            case 27:
                activity.action = ActivityAction.Comment
                match data["comment_type"]:
                    case 0:
                        activity.place = Project(data["comment_obj_id"],client_or_session)
                        activity.place.title = data["comment_obj_title"]
                    case 1:
                        activity.place = User(data["comment_obj_title"],client_or_session)
                        activity.place.id = data["comment_obj_id"]
                    case 2:
                        activity.place = Studio(data["comment_obj_id"],client_or_session)
                        activity.place.title = data["comment_obj_title"]
                activity.target = Comment(data["comment_id"],client_or_session,place=activity.place)
                activity.target.content = data["comment_fragment"]
                activity.target.commentee_id = data["recipient"] and data["recipient"]["pk"]
                activity.other = data["recipient"]

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
        _import()
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
        _import()
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