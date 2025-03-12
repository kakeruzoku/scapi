import datetime
from enum import Enum
import re
from typing import TYPE_CHECKING
import warnings

import bs4
from . import base
from ..others import common

if TYPE_CHECKING:
    from .session import Session
    from .comment import Comment
    from .studio import Studio
    from .project import Project
    from .user import User
    from ..cloud import cloud,server

class ActivityType(Enum):
    #[message/User/Studio/feed]
    unknown=0

    #Studio Activity
    StudioBecomeCurator=1 #[x o o o]
    StudioBecomeManager=2 #[o o o o]
    StudioBecomeHost=3 #[o x o o]
    StudioInviteCurator=4 #[o x x x]
    
    StudioRemoveCurator=5 #[x x o x]
    StudioRemoveProject=6 #[x x o x]

    StudioAddProject=7 #[x o o x]

    StudioUpdate=8 #[x x o x]
    StudioActivity=9 #[o x x x]
    StudioFollow=10 #[x o x x]

    #project
    ProjectLove=11 #[o o x x]
    ProjectFavorite=12 #[o o x x]
    ProjectShare=13 #[x o x o]
    ProjectRemix=14 #[x x x o]

    #User Activity
    UserFollowing=15 #[o o x o]

    #Forum
    ForumPost=16 #[o x x x]

    #Comment
    Comment=17 #[o x x x]

class Activity:
    id_name = "data"

    def __str__(self):
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
        self._raw:"dict|str" = None
        self.datetime:datetime.datetime|None = None
    
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

    def _load_project(self,tag:bs4.element.Tag,cs,ss) -> "base.Project":
        from .project import create_Partial_Project
        _project = create_Partial_Project(re.findall(r'\d+', tag["href"])[0],ClientSession=cs,session=ss)
        _project.title = tag.text
        return _project
    
    def _load_studio(self,tag:bs4.element.Tag,cs,ss):
        from .studio import create_Partial_Studio
        _studio = create_Partial_Studio(re.findall(r'\d+', tag["href"])[0],ClientSession=cs,session=ss)
        _studio.title = tag.text
        return _studio
    
    def _load_user(self,tag:bs4.element.Tag,cs,ss):
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
            self.target = self.place = self._load_project(span.next_sibling.next_sibling,cs,ss)
        elif "loved" in t:
            self.type = ActivityType.ProjectLove
            self.target = self.place = self._load_project(span.next_sibling.next_sibling,cs,ss)
        elif "added" in t:
            self.type = ActivityType.StudioAddProject
            self.place = self._load_studio(span.next_sibling.next_sibling,cs,ss)
            self.target = self._load_project(span.next_sibling.next_sibling.next_sibling.next_sibling,cs,ss)
        elif "was promoted to manager of" in t:
            self.type = ActivityType.StudioBecomeManager
            self.place = self._load_studio(span.next_sibling.next_sibling,cs,ss)
            self.target = None
        elif "became a curator of" in t:
            self.type = ActivityType.StudioBecomeCurator
            self.place = self._load_studio(span.next_sibling.next_sibling,cs,ss)
            self.target = None
        elif "is now following the studio" in t:
            self.type = ActivityType.StudioFollow
            self.place = self._load_studio(span.next_sibling.next_sibling,cs,ss)
            self.target = self._load_studio(span.next_sibling.next_sibling,cs,ss)
        elif "shared the project" in t:
            self.type = ActivityType.ProjectShare
            self.target = self.place = self._load_project(span.next_sibling.next_sibling,cs,ss)
        elif "is now following" in t:
            self.type = ActivityType.UserFollowing
            self.target = self.place = self._load_user(span.next_sibling.next_sibling,cs,ss)
        else:
            warnings.warn(f"unknown activitytype: {t} (user)")

class CloudActivity(base._BaseSiteAPI):

    def __str__(self):
        return f"<CloudActivity id:{self.project_id} user:{self.username} variable:{self.variable} value:{self.value}>"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        data:common.json_resp,
        scratch_session:"Session|None"=None,
        **entries
    ):
        super().__init__(None,None,ClientSession,scratch_session)

        self.method:str = data.get("method") or data.get("verb").replace("_var","")
        self.variable:str = data.get("name")
        self.value:str = data.get("value")
        self.username:str|None = data.get("user")
        self.project_id:int = data.get("project_id")

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