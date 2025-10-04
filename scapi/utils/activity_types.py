from typing import TypedDict,Literal,Union
from .types import OldUserPayload

class _ClassBaseActivity(TypedDict):
    actor:OldUserPayload
    datetime_created:str

class ClassBaseActivity(_ClassBaseActivity):
    type:int

class ClassUserFollowingActivity(_ClassBaseActivity):
    type:Literal[0]
    followed_username:str
    followed_user:OldUserPayload

class ClassStudioFollowingActivity(_ClassBaseActivity):
    type:Literal[1]
    title:str
    gallery:int

class ClassLoveActivity(_ClassBaseActivity):
    type:Literal[2]
    title:str
    recipient:OldUserPayload
    project:int

class ClassFavoriteActivity(_ClassBaseActivity):
    type:Literal[3]
    project_title:str
    project_creator:OldUserPayload
    project:int

class ClassProjectAddActivity(_ClassBaseActivity):
    type:Literal[7]
    project_title:str
    project:int
    recipient:OldUserPayload
    gallery_title:str
    gallery:int

class ClassProjectShareActivity(_ClassBaseActivity):
    type:Literal[10]
    title:str
    project:int
    is_reshare:bool

class ClassProjectRemixActivity(_ClassBaseActivity):
    type:Literal[11]
    title:str
    project:int
    parent_title:str
    parent:int
    recipient:OldUserPayload

class ClassStudioCreateActivity(_ClassBaseActivity): #わからん
    type:Literal[13]
    gallery:int

class ClassStudioUpdateActivity(_ClassBaseActivity):
    type:Literal[15]
    title:str
    gallery:int

class ClassProjectRemoveActivity(_ClassBaseActivity):
    type:Literal[19]
    project_title:str
    project:int
    recipient:OldUserPayload
    gallery_title:str
    gallery:int

class ClassStudioBecomeManagerActivity(_ClassBaseActivity):
    type:Literal[22]
    gallery_title:str
    gallery:int
    actor_username:str
    recipient:OldUserPayload|None
    recipient_username:str

class ClassEditProfileActivity(_ClassBaseActivity):
    type:Literal[25]
    changed_fields:str

class ClassCommentActivity(_ClassBaseActivity):
    type:Literal[27]
    comment_type:Literal[0,1,2]
    comment_fragment:str
    comment_id:int
    comment_obj_id:int
    comment_obj_title:str
    commentee_username:str|None
    recipient:OldUserPayload|None


ClassAnyActivity = Union[
    ClassUserFollowingActivity,
    ClassStudioFollowingActivity,
    ClassLoveActivity,
    ClassFavoriteActivity,
    ClassProjectAddActivity,
    ClassProjectShareActivity,
    ClassProjectRemixActivity,
    ClassStudioCreateActivity,
    ClassStudioUpdateActivity,
    ClassProjectRemoveActivity,
    ClassStudioBecomeManagerActivity,
    ClassEditProfileActivity,
    ClassCommentActivity
]

"""
S: studio
F: feed
M: message
U: user
"""

class _BaseActivity(TypedDict):
    datetime_created:str
    id:str|int
    actor_id:int
    actor_username:str

class BaseActivity(_BaseActivity):
    type:str

class StudioUpdateActivity(_BaseActivity): #S
    type:Literal["updatestudio"]

class StudioBecomeCuratorStudioActivity(_BaseActivity): #S
    type:Literal["becomecurator"]
    username:str

class StudioBecomeCuratorFeedActivity(StudioBecomeCuratorStudioActivity): #F
    gallery_id:int
    gallery_title:str

class StudioRemoveCuratorActivity(_BaseActivity): #S
    type:Literal["removecuratorstudio"]
    username:str

class StudioBecomeHostActivity(_BaseActivity): #S
    type:Literal["becomehoststudio"]
    admin_actor:bool
    former_host_username:str
    recipient_username:str

class StudioAddProjectActivity(_BaseActivity): #S
    type:Literal["addprojecttostudio"]
    project_id:int
    project_title:str

class StudioRemoveProjectActivity(_BaseActivity): #S
    type:Literal["removeprojectstudio"]
    project_id:int
    project_title:str

class StudioBecomeManagerStudioActivity(_BaseActivity): #S
    type:Literal["becomeownerstudio"]
    recipient_username:str

class StudioBecomeManagerFeedActivity(StudioBecomeManagerStudioActivity): #FM
    gallery_id:int
    gallery_title:str
    recipient_id:int

class ProjectShareActivity(_BaseActivity): #F
    type:Literal["shareproject"]
    project_id:int
    title:str

class ProjectLoveActivity(_BaseActivity): #FM
    type:Literal["loveproject"]
    project_id:int
    title:str

class ProjectFavoriteActivity(_BaseActivity): #FM
    type:Literal["favoriteproject"]
    project_id:int
    project_title:str

class StudioFollowActivity(_BaseActivity): #F
    type:Literal["followstudio"]
    gallery_id:int
    title:str

class ProjectRemixActivity(_BaseActivity): #FM
    type:Literal["remixproject"]
    project_id:int
    title:str
    parent_id:int
    parent_title:str

class UserJoinActivity(_BaseActivity): #M
    type:Literal["userjoin"]

class UserFollowActiviy(_BaseActivity): #MF
    type:Literal["followuser"]
    followed_user_id:int
    followed_username:str

class UserCommentActivity(_BaseActivity): #M
    type:Literal["addcomment"]
    comment_type:Literal[0,1,2]
    comment_fragment:str
    comment_id:int
    comment_obj_id:int
    comment_obj_title:str
    commentee_username:str|None

class StudioInviteCuratorActivity(_BaseActivity): #M
    type:Literal["curatorinvite"]
    gallery_id:int
    title:str

class ForumPostActivity(_BaseActivity): #M
    type:Literal["forumpost"]
    topic_id:int
    topic_title:str

class StudioActivityAcitivity(_BaseActivity): #M
    type:Literal["studioactivity"]
    gallery_id:int
    title:str


StudioAnyActivity = Union[
    StudioUpdateActivity,
    StudioBecomeCuratorStudioActivity,
    StudioRemoveCuratorActivity,
    StudioBecomeHostActivity,
    StudioAddProjectActivity,
    StudioRemoveProjectActivity,
    StudioBecomeManagerStudioActivity
]

FeedAnyActivity = Union[
    ProjectShareActivity,
    ProjectLoveActivity,
    ProjectFavoriteActivity,
    StudioBecomeManagerFeedActivity,
    StudioBecomeCuratorFeedActivity,
    StudioFollowActivity,
    ProjectRemixActivity,
    UserFollowActiviy
]

MessageAnyActivity = Union[
    UserJoinActivity,
    ProjectFavoriteActivity,
    ProjectLoveActivity,
    ProjectRemixActivity,
    UserFollowActiviy,
    StudioInviteCuratorActivity,
    StudioBecomeManagerFeedActivity,
    UserCommentActivity,
    ForumPostActivity,
    StudioActivityAcitivity
]