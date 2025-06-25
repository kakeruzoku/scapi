import datetime
from enum import Enum
import re
from typing import TYPE_CHECKING, Any
import warnings
import json

import bs4
from . import base
from ..others import common

if TYPE_CHECKING:
    from .session import Session
    from .comment import Comment
    from .studio import Studio
    from .project import Project
    from .user import User
    from .classroom import Classroom
    from ..cloud import cloud,server

class ActivityType(Enum):
    #[message/User/Studio/feed/class activity]
    unknown=0

    #Studio Activity
    StudioBecomeCurator=1 #[x o o o]
    StudioBecomeManager=2 #[o o o o]
    StudioBecomeHost=3 #[o x o o o]
    StudioInviteCurator=4 #[o x x x]
    
    StudioRemoveCurator=5 #[x x o x]
    StudioRemoveProject=6 #[x x o x]

    StudioAddProject=7 #[x o o x o]

    StudioUpdate=8 #[x x o x o]
    StudioActivity=9 #[o x x x]
    StudioFollow=10 #[x o x x o]

    #project
    ProjectLove=11 #[o o x x o]
    ProjectFavorite=12 #[o o x x o]
    ProjectShare=13 #[x o x o o]
    ProjectRemix=14 #[x x x o o]

    #User Activity
    UserFollowing=15 #[o o x o o]
    UserJoin=16 #[o o x x]
    UserChangeStatus=17 #[x x x x o]

    #Forum
    ForumPost=18 #[o x x x]

    #Comment
    Comment=19 #[o x x x]

class Activity:
    id_name = "data"

    def __repr__(self):
        return f"<Activity type:{self.type} id:{self.id} place:{self.place} actor:{self.actor} target:{self.target}>"

    def __init__(
        self,
        **entries
    ):
        self.id:int|None = None
        self.type:ActivityType = ActivityType.unknown
        self.actor:"User|None" = None
        self.target:"Comment|Studio|Project|User|None" = None
        self.place:"Studio|Project|User|None" = None
        self._raw:"dict|str" = {}
        self.datetime:datetime.datetime|None = None
        self.other:Any = None
    
    def _update_from_dict(self,obj:base._BaseSiteAPI,data:dict[str,str]) -> tuple[str,common.ClientSession, "Session"]:
        from .user import create_Partial_User
        self._raw = data.copy()
        self.datetime = common.to_dt(data["datetime_created"])
        self.actor = create_Partial_User(data["actor_username"],data["actor_id"],ClientSession=obj.ClientSession,session=obj.Session)
        return data["type"], obj.ClientSession, obj.Session

    def _update_from_message(self,session:"Session",data:dict[str,str]):
        from .comment import create_Partial_Comment
        from .studio import create_Partial_Studio
        from .project import create_Partial_Project
        from .user import create_Partial_User
        from .forum import create_Partial_ForumTopic
        t,cs,ss = self._update_from_dict(session,data)
        self.id = int(data["id"])
        if t == "followuser":
            self.type = ActivityType.UserFollowing
            self.place = self.target = create_Partial_User(data["followed_username"],data["followed_user_id"],ClientSession=cs,session=ss)
        elif t == "becomehoststudio":
            self.type = ActivityType.StudioBecomeHost
            self.target = session.create_Partial_myself()
            self.place = create_Partial_Studio(data["gallery_id"],ClientSession=cs,session=ss)
            self.place.title = data["gallery_title"]
        elif t == "becomeownerstudio":
            self.type = ActivityType.StudioBecomeManager
            self.target = session.create_Partial_myself()
            self.place = create_Partial_Studio(data["gallery_id"],ClientSession=cs,session=ss)
            self.place.title = data["gallery_title"]
        elif t == "curatorinvite":
            self.type = ActivityType.StudioInviteCurator
            self.target = session.create_Partial_myself()
            self.place = create_Partial_Studio(data["gallery_id"],ClientSession=cs,session=ss)
            self.place.title = data["title"]
        elif t == "studioactivity":
            self.type = ActivityType.StudioActivity
            self.target = self.place = create_Partial_Studio(data["gallery_id"],ClientSession=cs,session=ss)
            self.place.title = data["title"]
        elif t == "forumpost":
            self.type = ActivityType.ForumPost
            self.place = self.target = create_Partial_ForumTopic(data["topic_id"],ClientSession=cs,session=ss)
            self.place.title = data["topic_title"]
        elif t == "addcomment":
            self.type = ActivityType.Comment
            if data["comment_type"] == 0:
                self.place = create_Partial_Project(data["comment_obj_id"],ClientSession=cs,session=ss)
                self.place.title = data["comment_obj_title"]
            elif data["comment_type"] == 1:
                self.place = create_Partial_User(data["comment_obj_title"],data["comment_obj_id"],ClientSession=cs,session=ss)
            elif data["comment_type"] == 2:
                self.place = create_Partial_Studio(data["comment_obj_id"],ClientSession=cs,session=ss)
                self.place.title = data["comment_obj_title"]
            self.target = create_Partial_Comment(data["comment_id"],self.place,data["comment_fragment"],self.actor,ClientSession=cs,session=ss)
        elif t == "loveproject":
            self.type = ActivityType.ProjectLove
            self.place = self.target = create_Partial_Project(data["project_id"],session.create_Partial_myself(),ClientSession=cs,session=ss)
            self.place.title = data["title"]
        elif t == "favoriteproject":
            self.type = ActivityType.ProjectFavorite
            self.place = self.target = create_Partial_Project(data["project_id"],session.create_Partial_myself(),ClientSession=cs,session=ss)
            self.place.title = data["project_title"]
        elif t == "remixproject":
            self.type = ActivityType.ProjectRemix
            self.place = create_Partial_Project(data["parent_id"],session.create_Partial_myself(),ClientSession=cs,session=ss)
            self.place.title = data["parent_title"]
            self.target = create_Partial_Project(data["project_id"],session.create_Partial_myself(),ClientSession=cs,session=ss)
            self.place.title = data["title"]
        elif t == "userjoin":
            self.type = ActivityType.UserJoin
            self.place = self.target = None
        else:
            warnings.warn(f"unknown activitytype: {t} (message)")
        

    def _update_from_studio(self,studio:"Studio",data:dict[str,str]):
        from .project import create_Partial_Project
        from .user import create_Partial_User
        t,cs,ss = self._update_from_dict(studio,data)
        self.place = studio
        self.id = int(data["id"].split("-")[-1])
        if t == "becomecurator":
            self.type = ActivityType.StudioBecomeCurator
            self.target = create_Partial_User(data["username"],ClientSession=cs,session=ss)
        elif t == "becomeownerstudio":
            self.type = ActivityType.StudioBecomeManager
            self.target = create_Partial_User(data["recipient_username"],ClientSession=cs,session=ss)
        elif t == "becomehoststudio":
            self.type = ActivityType.StudioBecomeHost
            self.target = create_Partial_User(data["recipient_username"],ClientSession=cs,session=ss)
        elif t == "removecuratorstudio":
            self.type = ActivityType.StudioRemoveCurator
            self.target = create_Partial_User(data["username"],ClientSession=cs,session=ss)
        elif t == "updatestudio":
            self.type = ActivityType.StudioUpdate
            self.target = studio
        elif t == "addprojecttostudio":
            self.type = ActivityType.StudioAddProject
            self.target = create_Partial_Project(data["project_id"],ClientSession=cs,session=ss)
            self.target.title = data["project_title"]
        elif t == "removeprojectstudio":
            self.type = ActivityType.StudioRemoveProject
            self.target = create_Partial_Project(data["project_id"],ClientSession=cs,session=ss)
            self.target.title = data["project_title"]
        else:
            warnings.warn(f"unknown activitytype: {t} (studio)")

    def _update_from_feed(self,session:"Session",data:dict[str,str]):
        from .project import create_Partial_Project
        from .user import create_Partial_User
        from .studio import create_Partial_Studio
        self.id = int(data["id"])
        t,cs,ss = self._update_from_dict(session,data)
        if t == "shareproject":
            self.type = ActivityType.ProjectShare
            self.target = self.place = create_Partial_Project(data["project_id"],self.actor,ClientSession=cs,session=ss)
            self.target.title = data["title"]
        elif t == "loveproject":
            self.type = ActivityType.ProjectShare
            self.target = self.place = create_Partial_Project(data["project_id"],self.actor,ClientSession=cs,session=ss)
            self.target.title = data["title"]
        elif t == "favoriteproject":
            self.type = ActivityType.ProjectFavorite
            self.target = self.place = create_Partial_Project(data["project_id"],self.actor,ClientSession=cs,session=ss)
            self.target.title = data["project_title"]
        elif t == "followuser":
            self.type = ActivityType.UserFollowing
            self.target = self.place = create_Partial_User(data["followed_username"],data["followed_user_id"],ClientSession=cs,session=ss)
        elif t == "becomecurator":
            self.type = ActivityType.StudioBecomeCurator
            self.target = create_Partial_User(data["username"],ClientSession=cs,session=ss)
            self.place = create_Partial_Studio(data["gallery_id"],ClientSession=cs,session=ss)
            self.place.title = data["title"]
        elif t == "remixproject":
            self.type = ActivityType.ProjectRemix
            self.target = create_Partial_Project(data["project_id"],ClientSession=cs,session=ss)
            self.target.title = data["title"]
            self.place = create_Partial_Project(data["parent_id"],self.actor,ClientSession=cs,session=ss)
            self.place.title = data["parent_title"]
        elif t == "becomeownerstudio":
            self.type = ActivityType.StudioBecomeManager
            self.target = create_Partial_User(data["recipient_username"],ClientSession=cs,session=ss)
            self.place = create_Partial_Studio(data["gallery_id"],ClientSession=cs,session=ss)
            self.place.title = data["gallery_title"]
        elif t == "followstudio":
            self.type = ActivityType.StudioFollow
            self.target = self.place = create_Partial_Studio(data["gallery_id"],ClientSession=cs,session=ss)
            self.place.title = data["title"]
        elif t == "becomehoststudio":
            self.type = ActivityType.StudioBecomeHost
            self.target = create_Partial_User(data["recipient_username"],ClientSession=cs,session=ss)
            self.place = create_Partial_Studio(data["gallery_id"],ClientSession=cs,session=ss)
            self.place.title = data.get("title",data.get("gallery_title",None))
        else:
            warnings.warn(f"unknown activitytype: {t} (feed)")

    def _set_dt_from_html(self,text:str) -> None:
        _minute = _hour = _day = _week = _month = 0
        for i in text.replace("ago","").split(","):
            c = re.findall(r'\d+', i)
            c = 0 if c == [] else int(c[0])
            if "minute" in i: _minute = c
            elif "hour" in i: _hour = c
            elif "day" in i: _day = c
            elif "week" in i: _week = c
            elif "month" in i: _month = c
        td = datetime.timedelta(days=_day+(_week*7)+(_month*30),minutes=_minute,hours=_hour)
        dt = datetime.datetime.now() - td
        dt.astimezone(tz=datetime.timezone.utc)
        self.datetime = dt

    def _load_project_u(self,tag:bs4.element.Tag,cs,ss) -> "base.Project":
        from .project import create_Partial_Project
        _project = create_Partial_Project(re.findall(r'\d+', tag["href"])[0],ClientSession=cs,session=ss)
        _project.title = tag.text
        return _project
    
    def _load_studio_u(self,tag:bs4.element.Tag,cs,ss):
        from .studio import create_Partial_Studio
        _studio = create_Partial_Studio(re.findall(r'\d+', tag["href"])[0],ClientSession=cs,session=ss)
        _studio.title = tag.text
        return _studio
    
    def _load_user_u(self,tag:bs4.element.Tag,cs,ss):
        from .user import create_Partial_User
        return create_Partial_User(tag.text,ClientSession=cs,session=ss)


    def _update_from_user(self,user:"User",soup:bs4.element.Tag):
        self._raw = str(soup)
        cs,ss = user.ClientSession,user.Session
        self.actor = user
        self._set_dt_from_html(soup.find("span",{"class":"time"}).text)
        span = soup.find('div').find('span')
        t:str = span.next_sibling.strip()
        if "favorited" in t:
            self.type = ActivityType.ProjectFavorite
            self.target = self.place = self._load_project_u(span.next_sibling.next_sibling,cs,ss)
        elif "loved" in t:
            self.type = ActivityType.ProjectLove
            self.target = self.place = self._load_project_u(span.next_sibling.next_sibling,cs,ss)
        elif "added" in t:
            self.type = ActivityType.StudioAddProject
            self.place = self._load_studio_u(span.next_sibling.next_sibling,cs,ss)
            self.target = self._load_project_u(span.next_sibling.next_sibling.next_sibling.next_sibling,cs,ss)
        elif "was promoted to manager of" in t:
            self.type = ActivityType.StudioBecomeManager
            self.place = self._load_studio_u(span.next_sibling.next_sibling,cs,ss)
            self.target = None
        elif "became a curator of" in t:
            self.type = ActivityType.StudioBecomeCurator
            self.place = self._load_studio_u(span.next_sibling.next_sibling,cs,ss)
            self.target = None
        elif "is now following the studio" in t:
            self.type = ActivityType.StudioFollow
            self.place = self._load_studio_u(span.next_sibling.next_sibling,cs,ss)
            self.target = self._load_studio_u(span.next_sibling.next_sibling,cs,ss)
        elif "shared the project" in t:
            self.type = ActivityType.ProjectShare
            self.target = self.place = self._load_project_u(span.next_sibling.next_sibling,cs,ss)
        elif "is now following" in t:
            self.type = ActivityType.UserFollowing
            self.target = self.place = self._load_user_u(span.next_sibling.next_sibling,cs,ss)
        elif "joined Scratch" in t:
            self.type = ActivityType.UserJoin
            self.place = self.target = None
        else:
            warnings.warn(f"unknown activitytype: {t} (user)")

    def _load_user_cr(self,data:dict,is_student:bool,cs,ss):
        from .user import create_Partial_User
        _user = create_Partial_User(data.get("username"),ClientSession=cs,session=ss)
        _user.id = data.get("pk")
        _user.scratchteam = data.get("admin")
        return _user

    def _update_from_class(self,classroom:"Classroom",data:dict[str,Any]):
        from .project import create_Partial_Project
        from .user import create_Partial_User
        from .studio import create_Partial_Studio
        from .comment import create_Partial_Comment
        cs,ss = classroom.ClientSession,classroom.Session
        self.datetime = common.to_dt(data["datetime_created"])
        self.actor = self._load_user_cr(data.get("actor"),True,cs,ss)
        self._raw = data
        t:int = data.get("type")
        if t == 0:
            self.type = ActivityType.UserFollowing
            self.place = self.target = self._load_user_cr(data.get("followed_user"),False,cs,ss)
        elif t == 1:
            self.type = ActivityType.StudioFollow
            self.place = self.target = create_Partial_Studio(data.get("gallery"),ClientSession=cs,session=ss)
            self.place.title = data.get("title")
        elif t == 2:
            self.type = ActivityType.ProjectLove
            self.place = self.target = create_Partial_Project(data.get("project"),ClientSession=cs,session=ss)
            self.place.title = data.get("title")
            self.place.author = self._load_user_cr(data.get("recipient"),False,cs,ss)
        elif t == 3:
            self.type = ActivityType.ProjectFavorite
            self.place = self.target = create_Partial_Project(data.get("project"),ClientSession=cs,session=ss)
            self.place.title = data.get("title")
            self.place.author = self._load_user_cr(data.get("project_creator"),False,cs,ss)
        elif t == 7:
            self.type = ActivityType.StudioAddProject
            self.target = create_Partial_Project(data.get("project"),ClientSession=cs,session=ss)
            self.target.title = data.get("project_title")
            self.target.author = self._load_user_cr(data.get("recipient"),False,cs,ss)
            self.place = create_Partial_Studio(data.get("gallery"),ClientSession=cs,session=ss)
            self.place.title = data.get("gallery_title")
        elif t == 10:
            self.type = ActivityType.ProjectShare
            self.place = self.target = create_Partial_Project(data.get("project"),ClientSession=cs,session=ss)
            self.place.title = data.get("title")
            self.place.author = self.actor
            self.other = data.get("is_reshare")
        elif t == 11:
            self.type = ActivityType.ProjectRemix
            self.target = create_Partial_Project(data.get("project"),ClientSession=cs,session=ss)
            self.target.title = data.get("title")
            self.target.author = self.actor
            self.place = create_Partial_Project(data.get("parent"),ClientSession=cs,session=ss)
            self.place.title = data.get("parent_title")
        elif t == 13: #スタジオ作成?
            self.type = ActivityType.StudioBecomeHost
            self.target = self.place = create_Partial_Studio(data.get("gallery"),ClientSession=cs,session=ss)
        elif t == 15:
            self.type = ActivityType.StudioUpdate
            self.target = self.place = create_Partial_Studio(data.get("gallery"),ClientSession=cs,session=ss)
            self.target.title = data.get("title")
        elif t == 19:
            self.type = ActivityType.StudioRemoveProject
            self.target = create_Partial_Project(data.get("project"),ClientSession=cs,session=ss)
            self.target.title = data.get("project_title")
            self.target.author = self._load_user_cr(data.get("recipient"),False,cs,ss)
            self.place = create_Partial_Studio(data.get("gallery"),ClientSession=cs,session=ss)
            self.place.title = data.get("gallery_title")
        elif t == 22:
            self.type = ActivityType.StudioBecomeManager
            if data.get("recipient") is None:
                self.target = self.actor
            else:
                self.target = self._load_user_cr(data.get("recipient"),False,cs,ss)
            self.place = create_Partial_Studio(data.get("gallery"),ClientSession=cs,session=ss)
            self.place.title = data.get("gallery_title")
        elif t == 25:
            self.type = ActivityType.UserChangeStatus
            self.place = self.target = self.actor
            self.other = json.loads(data.get("changed_fields"))
        elif t == 27: #recipient commentee_username x
            self.type = ActivityType.Comment
            if data["comment_type"] == 0:
                self.place = create_Partial_Project(data["comment_obj_id"],ClientSession=cs,session=ss)
                self.place.title = data["comment_obj_title"]
            elif data["comment_type"] == 1:
                self.place = create_Partial_User(data["comment_obj_title"],data["comment_obj_id"],ClientSession=cs,session=ss)
            elif data["comment_type"] == 2:
                self.place = create_Partial_Studio(data["comment_obj_id"],ClientSession=cs,session=ss)
                self.place.title = data["comment_obj_title"]
            self.target = create_Partial_Comment(data["comment_id"],self.place,data["comment_fragment"],self.actor,ClientSession=cs,session=ss)
        else:
            warnings.warn(f"unknown activitytype: {t} (class activity)")
            

        

class CloudActivity(base._BaseSiteAPI):
    id_name = "data"

    def __repr__(self):
        return f"<CloudActivity method:{self.method} id:{self.project_id} user:{self.username} variable:{self.variable} value:{self.value}>"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        data:dict[str,Any],
        scratch_session:"Session|None"=None,
        **entries
    ):
        super().__init__(None,None,ClientSession,scratch_session)

        self.method:str = data.get("method") or data.get("verb","").replace("_var","")
        self.variable:str = str(data.get("name")).removeprefix("☁ ")
        if data.get("value") is None: self.value:str = None
        else: self.value:str = str(data.get("value")).removeprefix("☁ ")
        self.username:str|None = data.get("user")
        self.project_id:int = data.get("project_id")
        self.datetime:datetime.datetime = common.to_dt_timestamp_1000(data.get("timestamp")) or data.get("datetime")

        self.cloud:"cloud._BaseCloud|server.CloudServerConnection|None" = data.get("cloud")

    async def update(self):
        pass

    def _update_from_dict(self, data):
        pass

    async def get_user(self) -> "User":
        common.no_data_checker(self.username)
        from .user import User
        return await base.get_object(self.ClientSession,self.username,User,self.Session)
    
    async def get_project(self) -> "Project":
        common.no_data_checker(self.project_id)
        from .project import Project
        return await base.get_object(self.ClientSession,self.project_id,Project,self.Session)