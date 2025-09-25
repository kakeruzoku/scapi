from typing import Generic, Literal, TypeVar, TypedDict, Required, NotRequired

class NoElementsPayload(TypedDict):
    pass

DecodedSessionID = TypedDict(
    "DecodedSessionID",{
        "token":str,
        "username":str,
        "login-ip":str,
        "_auth_user_id":str
    }
)

_T = TypeVar("_T")

class OldAnyObjectPayload(TypedDict,Generic[_T]):
    fields:_T
    model:str
    pk:int

class AnySuccessPayload(TypedDict):
    success:bool

class SessionStatusUserPayload(TypedDict):
    id:int
    banned:bool
    should_vpn:bool
    username:str
    token:str
    thumbnailUrl:str
    dateJoined:str
    email:str
    birthYear:int|None
    birthMonth:int|None
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
    mute_status:"CommentMuteStatusPayload|NoElementsPayload"

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

class MessageCountPayload(TypedDict):
    count:int

class ScratcherInvitePayload(TypedDict):
    id:int
    datetime_created:str
    unread:int
    actor_id:int
    invitee_id:int

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

class UserHistoryPayload(TypedDict):
    joined:str

class UserProfilePayload(TypedDict,total=False):
    id:int
    #images
    status:str
    bio:str
    country:str

class UserPayload(TypedDict,total=False):
    id:int
    username:Required[str]
    scratchteam:bool
    history:UserHistoryPayload
    profile:UserProfilePayload

class OldUserPayload(TypedDict):
    username:str
    pk:int
    thumbnail_url:str
    admin:bool

class StudentPayload(TypedDict):
    educator_can_unban:bool
    is_banned:bool
    thumbnail_url:str
    user:OldUserPayload

class StudentPasswordRestPayliad(AnySuccessPayload):
    user:OldUserPayload

class UserFeaturedProjectPayload(TypedDict):
    creator:str
    thumbnail_url:str
    id:str
    datetime_modified:str
    title:str

class UserFeaturedUserPayload(TypedDict):
    username:str
    pk:int

class UserFeaturedPayload(TypedDict):
    featured_project_label_name:str
    featured_project_data:UserFeaturedProjectPayload|None
    featured_project:int|None
    thumbnail_url:str
    user:UserFeaturedUserPayload
    featured_project_label_id:int|None
    id:int

class UserMessageCountPayload(TypedDict):
    count:int

class ProjectHistoryPayload(TypedDict):
    created:str
    modified:str
    shared:str

class ProjectStatsPayload(TypedDict):
    views:int
    loves:int
    favorites:int
    remixes:int

class ProjectRemixPayload(TypedDict):
    parent:int|None
    root:int|None

class ProjectPayload(TypedDict,total=False):
    id:Required[int]
    title:str
    description:str
    instructions:str
    visibility:Literal["visible","notvisible"]
    public:bool
    comments_allowed:bool
    is_published:bool
    author:UserPayload
    image:str
    #images
    history:ProjectHistoryPayload
    stats:ProjectStatsPayload
    remix:ProjectRemixPayload
    project_token:str

class OldProjectPayload(TypedDict):
    view_count:int
    favorite_count:int
    remixers_count:int
    creator:OldUserPayload
    title:str
    isPublished:bool
    datetime_created:str
    thumbnail_url:str
    visibility:Literal["visible","trshbyusr"]
    love_count:int
    datetime_modified:str|None
    uncached_thumbnail_url:str
    thumbnail:str
    datetime_shared:str|None
    commenters_count:str

class OldProjectEditPayload(TypedDict):
    creator:str
    thumbnail_url:str
    id:int
    datetime_modified:str
    title:str

ProjectServerPayload = TypedDict(
    "ProjectServerPayload",{
        "status":str,
        "autosave-interval":str,
        "content-name":NotRequired[str],
        "content-title":NotRequired[str]
    }
)

class ProjectLovePayload(TypedDict):
    projectId:str
    userLove:bool
    statusChanged:bool

class ProjectFavoritePayload(TypedDict):
    projectId:str
    userFavorite:bool
    statusChanged:bool

class ProjectVisibilityPayload(TypedDict):
    projectId:int
    creatorId:int
    deleted:bool
    censored:bool
    censoredByAdmin:bool
    censoredByCommunity:bool
    reshareable:bool
    message:str

class ReportPayload(AnySuccessPayload):
    moderation_status:str

RemixTreeDatetimePayload = TypedDict(
    "RemixTreeDatetimePayload",
    {"$date":int}
)

class RemixTreePayload(TypedDict):
    username:str
    favorite_count:str
    moderation_status:str
    ctime:NotRequired[RemixTreeDatetimePayload]
    title:str
    datetime_created:RemixTreeDatetimePayload
    children:list[int]
    parent_id:int|None
    visibility:str
    love_count:int
    datetime_modified:NotRequired[RemixTreeDatetimePayload]
    mtime:NotRequired[RemixTreeDatetimePayload]
    id:int
    datetime_shared:NotRequired[RemixTreeDatetimePayload]
    is_published:bool

class StudioHistoryPayload(TypedDict):
    created:str
    modified:str

class StudioStatsPayload(TypedDict):
    comments:int
    followers:int
    managers:int
    projects:int

class StudioCreatedPayload(AnySuccessPayload):
    redirect:str

class StudioPayload(TypedDict,total=False):
    id:Required[int]
    title:str
    host:int
    description:str
    visibility:Literal["visible"]
    public:Literal[True]
    open_to_all:bool
    comments_allowed:bool
    image:str
    history:StudioHistoryPayload
    stats:StudioStatsPayload

class OldStudioPayload(TypedDict):
    commenters_count:int
    curators_count:int
    datetime_created:str
    datetime_modified:str
    owner:OldUserPayload
    projecters_count:int
    thumbnail_url:str
    title:str
    description:NotRequired[str]

class StudioRolePayload(TypedDict):
    manager:bool
    curator:bool
    invited:bool
    following:bool

class StudioClassroomPayload(TypedDict):
    id:int

class CommentPayload(TypedDict,total=False):
    id:Required[int]
    parent_id:int|None
    commentee_id:int|None
    content:str
    datetime_created:str
    datetime_modified:str
    visibility:str
    author:UserPayload
    reply_count:int

class CommentPostPayload(TypedDict):
    content:str
    parent_id:int|Literal[""]
    commentee_id:int|Literal[""]

class CommentMuteStatusOffensePayload(TypedDict):
    createdAt:float
    expiresAt:float
    messageType:str

class CommentMuteStatusPayload(TypedDict):
    offenses:list[CommentMuteStatusOffensePayload]
    showWarning:bool
    muteExpiresAt:float
    currentMessageType:str

class CommentFailureStatusPayload(TypedDict):
    mute_status:CommentMuteStatusPayload|NoElementsPayload

class CommentFailurePayload(TypedDict):
    status:CommentFailureStatusPayload
    rejected:str

class CommentFailureOldPayload(TypedDict):
    mute_status:NotRequired[CommentMuteStatusPayload|NoElementsPayload]
    error:str

class ClassCreatedPayload(AnySuccessPayload):
    msg:str
    id:int
    title:str

class ClassroomPayload(TypedDict):
    id:int
    title:str
    description:str
    status:str
    data_start:str
    data_end:str|None
    #images
    educator:UserPayload

class OldBaseClassroomPayload(TypedDict):
    datetime_created:str
    gallery_count:int
    student_count:int
    thumbnail_url:str
    title:str
    token:str
    unread_alert_count:int

class OldAllClassroomPayload(OldBaseClassroomPayload):
    visibility:Literal["visible","closed"]
    commenters_count:int
    educator_profile:UserFeaturedPayload

class OldIdClassroomPayload(OldBaseClassroomPayload):
    id:int
    description:str
    status:str
    educator:UserFeaturedUserPayload

class ClassTokenGeneratePayload(AnySuccessPayload):
    reg_link:str
    expires_at:str
    error:str

class ClassStudioCreatePayload(AnySuccessPayload):
    msg:str
    gallery_id:int
    gallery_title:str

class NewsPayload(TypedDict):
    id:int
    stamp:str
    headline:str
    url:str
    image:str
    copy:str

class BaseCommunityFeaturedObjectPayload(TypedDict):
    id:int
    title:str

class CommunityFeaturedProjectPayload(BaseCommunityFeaturedObjectPayload):
    love_count:int
    creator:str

class CommunityFeaturedRemixProjectPayload(CommunityFeaturedProjectPayload):
    remixers_count:int

class CommunityFeaturedDesignProjectPayload(CommunityFeaturedRemixProjectPayload):
    gallery_id:int
    gallery_title:str

class CommunityFeaturedPayload(TypedDict):
    community_featured_projects:list[CommunityFeaturedProjectPayload]
    community_featured_studios:list[BaseCommunityFeaturedObjectPayload]
    community_most_loved_projects:list[CommunityFeaturedProjectPayload]
    community_most_remixed_projects:list[CommunityFeaturedRemixProjectPayload]
    community_newest_projects:list[CommunityFeaturedProjectPayload]
    scratch_design_studio:list[CommunityFeaturedDesignProjectPayload]

class CheckAnyPayload(TypedDict):
    msg:str

class TranslatePayload(TypedDict):
    result:str

class TranslateSupportedLanguagePayload(TypedDict):
    code:str
    name:str

class TranslateSupportedPayload(TypedDict):
    result:list[TranslateSupportedLanguagePayload]

class WSCloudActivityPayload(TypedDict):
    method:Literal["set"]
    name:str
    value:str

class CloudLogPayload(TypedDict):
    verb:str
    name:str
    value:int|float|str
    timestamp:int
    user:str

class OcularNotFoundPayload(TypedDict):
    error:str

class OcularMetaPayload(TypedDict):
    updated:str
    updatedBy:str

class OcularFoundPayload(TypedDict):
    _id:int
    name:str
    status:str
    color:str
    meta:OcularMetaPayload
    
OcularPayload = OcularNotFoundPayload|OcularFoundPayload

search_mode = Literal["trending","popular"]
explore_query = Literal["*","animations","art","games","music","stories","tutorial"]|str