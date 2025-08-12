from typing import Literal, TypedDict
from typing_extensions import NotRequired


DecodedSessionID = TypedDict(
    "DecodedSessionID",{
        "token":str,
        "username":str,
        "login-ip":str,
        "_auth_user_id":str
    }
)

class SessionStatusUserPayload(TypedDict):
    id:int
    banned:bool
    should_vpn:bool
    username:str
    token:str
    thumbnailUrl:str
    dateJoined:str
    email:str
    birthYear:int
    birthMonth:int
    gender:str
    classroomId:NotRequired[int]

class SessionStatusPermissionsPayload(TypedDict):
    admin:bool
    scratcher:bool
    new_scratcher:bool
    invited_scratcher:bool
    social:bool
    educator:bool
    educator_invitee:bool
    student:bool
    mute_status:dict

class SessionStatusFlagsPayload(TypedDict):
    must_reset_password:bool
    must_complete_registration:bool
    has_outstanding_email_confirmation:bool
    show_welcome:bool
    confirm_email_banner:bool
    unsupported_browser_banner:bool
    with_parent_email:bool
    project_comments_enabled:bool
    gallery_comments_enabled:bool
    userprofile_comments_enabled:bool
    everything_is_totally_normal:bool


class SessionStatusPayload(TypedDict):
    user:SessionStatusUserPayload
    permissions:SessionStatusPermissionsPayload
    flags:SessionStatusFlagsPayload

class LoginFailurePayload(TypedDict):
    username:str
    num_tries:NotRequired[int]
    redirect:NotRequired[str]
    success:Literal[0]
    msg:str
    messages:list
    id:None

class LoginSuccessPayload(TypedDict):
    username:str
    token:str
    num_tries:int
    success:Literal[1]
    msg:str
    messages:list
    id:int