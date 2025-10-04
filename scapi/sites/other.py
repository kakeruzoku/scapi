from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Literal, TypedDict

from ..utils.types import (
    CheckAnyPayload,
    TranslatePayload,
    TranslateSupportedPayload,
    TotalSiteStatusPayload,
    MonthlySiteTrafficPayload,
    MonthlyActivityGraphPayload,
    MonthlyActivityPayload
)
from ..utils.common import (
    UNKNOWN,
    MAYBE_UNKNOWN,
    dt_from_timestamp
)

if TYPE_CHECKING:
    from ..utils.client import HTTPClient

class UsernameStatus(Enum):
    valid="valid username"
    exist="username exists"
    invalid="invalid username"
    bad="bad username"

async def check_username(client:"HTTPClient",username:str) -> MAYBE_UNKNOWN[UsernameStatus]:
    """
    ユーザー名が利用可能か確認する。

    Args:
        client (HTTPClient): 通信に使用するHTTPClient
        username (str): 確認したいユーザー名

    Returns:
        MAYBE_UNKNOWN[UsernameStatus]:
    """
    response = await client.get(f"https://api.scratch.mit.edu/accounts/checkusername/{username}")
    data:CheckAnyPayload = response.json()
    msg = data.get("msg")
    if msg in UsernameStatus:
        return UsernameStatus(data.get("msg"))
    else:
        return UNKNOWN
    
class PasswordStatus(Enum):
    valid="valid password"
    invalid="invalid password"
    
async def check_password(client:"HTTPClient",password:str) -> MAYBE_UNKNOWN[PasswordStatus]:
    """
    パスワードが使用可能か確認する。

    Args:
        client (HTTPClient): 通信に使用するHTTPClient
        password (str): 確認したいパスワード

    Returns:
        MAYBE_UNKNOWN[PasswordStatus]:
    """
    response = await client.post(f"https://api.scratch.mit.edu/accounts/checkpassword/",json={"password":password})
    data:CheckAnyPayload = response.json()
    msg = data.get("msg")
    if msg in PasswordStatus:
        return PasswordStatus(data.get("msg"))
    else:
        return UNKNOWN

class EmailStatus(Enum):
    vaild="valid email"
    invaild="Scratch is not allowed to send email to this address."

async def check_email(client:"HTTPClient",email:str) -> MAYBE_UNKNOWN[EmailStatus]:
    """
    メールアドレスが利用可能か確認する。

    Args:
        client (HTTPClient): 通信に使用するHTTPClient
        email (str): 確認したいメールアドレス

    Returns:
        MAYBE_UNKNOWN[EmailStatus]:
    """
    response = await client.get(f"https://scratch.mit.edu/accounts/check_email/",params={"email":email})
    data:CheckAnyPayload = response.json()[0]
    msg = data.get("msg")
    if msg in EmailStatus:
        return EmailStatus(data.get("msg"))
    else:
        return UNKNOWN
    
async def translation(client:"HTTPClient",language:str,text:str) -> str:
    """
    テキストを翻訳する。

    Args:
        client (HTTPClient): 使用するHTTPClient
        language (str): 翻訳先の言語コード
        text (str): 翻訳するテキスト

    Returns:
        str: 翻訳されたテキスト
    """
    response = await client.get(
        "https://translate-service.scratch.mit.edu/translate",
        params={
            "language":language,
            "text":text
        }
    )
    data:TranslatePayload = response.json()
    return data.get("result")

async def get_supported_translation_language(client:"HTTPClient") -> dict[str,str]:
    """
    翻訳でサポートされているテキストを取得する。

    Args:
        client (HTTPClient): 使用するHTTPClient

    Returns:
        dict[str,str]: 対応している言語の言語コードと名前のペア
    """
    response = await client.get("https://translate-service.scratch.mit.edu/supported")
    data:TranslateSupportedPayload = response.json()
    return {i.get("code"):i.get("name") for i in data.get("result")}

async def tts(client:"HTTPClient",language:str,type:Literal["male","female"],text:str) -> bytes:
    """
    読み上げ音声を取得する。

    Args:
        client (HTTPClient): 使用するHTTPClient
        language (str): 使用する言語 (en-US形式)
        type (Literal["male","famale"])]: 話す声の種類
        text (str): 話す内容

    Returns:
        bytes:
    """
    response = await client.get(
        "https://synthesis-service.scratch.mit.edu/synth",
        params={
            "locale":language,
            "gender":type,
            "text":text
        }
    )
    return response.data

@dataclass
class TotalSiteStats:
    project_count:int
    user_count:int
    studio_comment_count:int
    profile_comment_count:int
    studio_count:int
    comment_count:int
    project_comment_count:int
    _timestamp:float

async def get_total_site_stats(client:HTTPClient) -> TotalSiteStats:
    """
    全体の統計情報を取得する

    Args:
        client (HTTPClient): 通信に使用するHTTPClient

    Returns:
        TotalSiteStats:
    """
    response = await client.get("https://scratch.mit.edu/statistics/data/daily/")
    data:TotalSiteStatusPayload = response.json()
    return TotalSiteStats(
        project_count=data.get("PROJECT_COUNT"),
        user_count=data.get("USER_COUNT"),
        studio_comment_count=data.get("STUDIO_COMMENT_COUNT"),
        profile_comment_count=data.get("PROFILE_COMMENT_COUNT"),
        studio_count=data.get("STUDIO_COUNT"),
        comment_count=data.get("COMMENT_COUNT"),
        project_comment_count=data.get("PROJECT_COMMENT_COUNT"),
        _timestamp=data.get("_TS")
    )

@dataclass
class MonthlySiteTraffic:
    pageviews:int
    users:int
    sessions:int
    _timestamp:float

async def get_monthly_site_traffic(client:HTTPClient) -> MonthlySiteTraffic:
    """
    月のアクティビティ数を取得する。

    Args:
        client (HTTPClient): 通信に使用するHTTPClient

    Returns:
        MonthlySiteTraffic:
    """
    response = await client.get("https://scratch.mit.edu/statistics/data/monthly-ga/")
    data:MonthlySiteTrafficPayload = response.json()
    return MonthlySiteTraffic(
        pageviews=data.get("pageviews"),
        users=data.get("users"),
        sessions=data.get("sessions"),
        _timestamp=data.get("_TS")
    )



GraphData = list[tuple[int, int]]

@dataclass
class CommentData:
    """コメント統計データ"""
    project: GraphData
    studio: GraphData
    profile: GraphData

@dataclass
class ActivityData:
    """アクティビティ統計データ"""
    new_projects: GraphData
    new_users: GraphData
    new_comments: GraphData

@dataclass
class ActiveUserData:
    """アクティブユーザー統計データ"""
    project_creators: GraphData
    comment_creators: GraphData

@dataclass
class ProjectData:
    """プロジェクト統計データ"""
    new_projects: GraphData
    remix_projects: GraphData

@dataclass
class AgeDistributionData:
    """年齢分布データ"""
    registration_age: GraphData

@dataclass
class MonthlyActivity:
    """
    月間アクティビティ統計情報を表す
    """
    _timestamp: float
    comment_data: CommentData
    activity_data: ActivityData
    active_user_data: ActiveUserData
    project_data: ProjectData
    age_distribution_data: AgeDistributionData
    country_distribution: dict[str,int]

def _parse_graph_data(raw_data: list[MonthlyActivityGraphPayload], index: int) -> GraphData:
    if index < len(raw_data) and "values" in raw_data[index]:
        return [(d["x"], d["y"]) for d in raw_data[index]["values"]]
    return []

async def get_monthly_activity(client: HTTPClient) -> MonthlyActivity:
    """
    月間アクティビティ統計情報を取得する。

    Args:
        client (HTTPClient): 通信に使用するHTTPClient

    Returns:
        MonthlyActivity:
    """
    response = await client.get("https://scratch.mit.edu/statistics/data/monthly/")
    data:MonthlyActivityPayload = response.json()

    raw_comment_data = data.get("comment_data", [])
    comment_data = CommentData(
        project=_parse_graph_data(raw_comment_data, 0),
        studio=_parse_graph_data(raw_comment_data, 1),
        profile=_parse_graph_data(raw_comment_data, 2),
    )

    raw_activity_data = data.get("activity_data", [])
    activity_data = ActivityData(
        new_projects=_parse_graph_data(raw_activity_data, 0),
        new_users=_parse_graph_data(raw_activity_data, 1),
        new_comments=_parse_graph_data(raw_activity_data, 2),
    )

    raw_active_user_data = data.get("active_user_data", [])
    active_user_data = ActiveUserData(
        project_creators=_parse_graph_data(raw_active_user_data, 0),
        comment_creators=_parse_graph_data(raw_active_user_data, 1),
    )

    raw_project_data = data.get("project_data", [])
    project_data = ProjectData(
        new_projects=_parse_graph_data(raw_project_data, 0),
        remix_projects=_parse_graph_data(raw_project_data, 1),
    )

    raw_age_distribution_data = data.get("age_distribution_data", [])
    age_distribution_data = AgeDistributionData(
        registration_age=_parse_graph_data(raw_age_distribution_data, 0)
    )

    return MonthlyActivity(
        _timestamp=data.get("_TS", 0.0),
        comment_data=comment_data,
        activity_data=activity_data,
        active_user_data=active_user_data,
        project_data=project_data,
        country_distribution=data.get("country_distribution", {}),
        age_distribution_data=age_distribution_data,
    )