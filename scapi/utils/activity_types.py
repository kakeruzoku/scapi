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

class _BaseActivity(TypedDict):
    datetime_created:str
    id:str
    actor_id:int
    actor_username:str

class BaseActivity(_BaseActivity):
    type:str

class StudioUpdateActivity(_BaseActivity):
    type:Literal["updatestudio"]

class StudioBecomeCuratorActivity(_BaseActivity):
    type:Literal["becomecurator"]
    username:str

class StudioRemoveCuratorActivity(_BaseActivity):
    type:Literal["removecuratorstudio"]
    username:str

class StudioBecomeHostActivity(_BaseActivity):
    type:Literal["becomehoststudio"]
    admin_actor:bool
    former_host_username:str
    recipient_username:str

class StudioAddProjectActivity(_BaseActivity):
    type:Literal["addprojecttostudio"]
    project_id:int
    project_title:str

class StudioRemoveProjectActivity(_BaseActivity):
    type:Literal["removeprojectstudio"]
    project_id:int
    project_title:str

class StudioBecomeManagerActivity(_BaseActivity):
    type:Literal["becomeownerstudio"]
    recipient_username:str



StudioAnyActivity = Union[
    StudioUpdateActivity,
    StudioBecomeCuratorActivity,
    StudioRemoveCuratorActivity,
    StudioBecomeHostActivity,
    StudioAddProjectActivity,
    StudioRemoveProjectActivity,
    StudioBecomeManagerActivity
]