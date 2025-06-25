import datetime
import re
from typing import AsyncGenerator, Literal, TYPE_CHECKING, overload
import aiohttp

import bs4

from ..others import  common
from ..others import error as exception
from . import base,user,studio,activity

if TYPE_CHECKING:
    from . import session

class Classroom(base._BaseSiteAPI):
    id_name = "id"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        id:int,
        scratch_session:"session.Session|None"=None,
        **entries
    ):
        
        super().__init__("get",f"https://api.scratch.mit.edu/classrooms/{id}",ClientSession,scratch_session)

        self.id:int = common.try_int(id)
        self.classtoken:str|None = None
        self.title:str = None
        self._created:str = None
        self.created:datetime.datetime = None
        self.educator:"user.User" = None

        self._student_count:int|None = None
        self._studio_count:int|None = None
        self.commenter_count:int|None = None

        self.about_class:str = None
        self.wiwo:str = None
        
    def _update_from_dict(self, data:dict):
        self.title = data.get("title",self.title)
        self._add_datetime("created",data.get("date_start"))
        _author:dict = data.get("educator",{})
        self.educator = user.User(self.ClientSession,_author.get("username",None),self.Session)
        self.educator._update_from_dict(_author)

        self.about_class = data.get("description",self.about_class)
        self.wiwo = data.get("status",self.wiwo)

    def _update_from_old_dict(self, fields:dict):
        #closed : "closed"

        self._student_count = fields.get("student_count",self._student_count)
        self.title = fields.get("title",self.title)
        self._add_datetime("created",fields.get("datetime_created"))
        self.classtoken = fields.get("token",self.classtoken)
        self.commenter_count = fields.get("commenters_count",self.commenter_count)
        _user:dict = fields.get("educator_profile",{})
        _user:dict = _user.get("user",_user) or fields.get("educator")
        self.educator = user.create_Partial_User(_user.get("username"),_user.get("pk"),ClientSession=self.ClientSession,session=self.Session)
        self._studio_count = fields.get("gallery_count",self._studio_count)

        self.about_class = fields.get("description",self.about_class)
        self.wiwo = fields.get("status",self.wiwo)

    def _update_from_mystuff(self, data:dict):
        self._update_from_old_dict(data.get("fields"))


    @property
    def _is_owner(self) -> bool:
        from .session import Session
        if isinstance(self.Session,Session):
            if self.Session.username == (self.educator and self.educator.username):
                return True
        return False
    
    def _is_owner_raise(self) -> None:
        if self.check and not self._is_owner:
            raise exception.NoPermission

    def studios(self, *, start_page=1, end_page=1, is_website:bool|None=None) -> AsyncGenerator[studio.Studio, None]:
        if is_website is None: is_website = not self._is_owner
        if is_website:
            return self._studios_from_website(start_page=start_page,end_page=end_page)
        else:
            return base.get_object_iterator(
                self.ClientSession,f"https://scratch.mit.edu/site-api/classrooms/studios/{self.id}/",
                "pk",studio.Studio, self.Session,
                limit=end_page-start_page+1 ,offset=start_page, max_limit=1, is_page=True,
                update_func_name="_update_from_mystuff"
            )

    async def _studios_from_website(self, *, start_page=1, end_page=1) -> AsyncGenerator[studio.Studio, None]:
        for i in range(start_page,end_page+1):
            r = await self.ClientSession.get(f"https://scratch.mit.edu/classes/{self.id}/studios/?page={i}",check=False)
            if r.status_code == 404:
                return
            soup = bs4.BeautifulSoup(r.text, "html.parser")
            projects:bs4.element.ResultSet[bs4.element.Tag] = soup.find_all("li", {"class": "gallery thumb item"})
            if len(projects) == 0:
                return
            for _project in projects:
                id = common.split_int(str(_project),"a href=\"/studios/","/")
                if id is None: continue
                _title = _project.find("span",{"class":"title"})
                _obj = studio.Studio(self.ClientSession,id,self.Session)
                _obj.author_id = self.educator.id
                _obj.title = common.split(str(_title),f"/\">","</a>").strip()
                yield _obj
    
    async def studio_count(self) -> int:
        return await base.get_count(self.ClientSession,f"https://scratch.mit.edu/classes/{self.id}/studios/","Class Studios (",")")
    
    def students(self, *, start_page=1, end_page=1, is_website:bool|None=None) -> AsyncGenerator[user.User, None]:
        if is_website is None: is_website = not self._is_owner
        if is_website:
            return self._users_from_website(start_page=start_page,end_page=end_page)
        else:
            return base.get_object_iterator(
                self.ClientSession,f"https://scratch.mit.edu/site-api/classrooms/students/{self.id}/",
                "pk",user.User, self.Session,
                limit=end_page-start_page+1 ,offset=start_page, max_limit=1, is_page=True,
                update_func_name="_update_from_student_dict"
            )

    async def _users_from_website(self, *, start_page=1, end_page=1) -> AsyncGenerator[user.User, None]:
        for i in range(start_page,end_page+1):
            r = await self.ClientSession.get(f"https://scratch.mit.edu/classes/{self.id}/students/?page={i}",check=False)
            if r.status_code == 404:
                return
            soup = bs4.BeautifulSoup(r.text, "html.parser")
            projects:bs4.element.ResultSet[bs4.element.Tag] = soup.find_all("li", {"class": "user thumb item"})
            if len(projects) == 0:
                return
            for _project in projects:
                username = common.split(str(_project),"a href=\"/users/","/")
                _icon = _project.find("img",{"class":"lazy"})
                _obj = user.User(self.ClientSession,username,self.Session)
                _obj.id = common.split_int(_icon["data-original"],"/user/","_")
                yield _obj

    async def student_count(self) -> int:
        return await base.get_count(self.ClientSession,f"https://scratch.mit.edu/classes/{self.id}/students/","Students (",")")
    
    async def edit(
            self,
            title:str|None=None,
            about_class:str|None=None,
            wiwo:str|None=None,
            open:bool|None=None
        ):
        self._is_owner_raise()
        data = {}
        if title is not None: data["title"] = title
        if about_class is not None: data["description"] = about_class
        if wiwo is not None: data["status"] = wiwo
        if open is not None: data["visibility"] = "visible" if open else "closed"
        r = await self.ClientSession.put(f"https://scratch.mit.edu/site-api/classrooms/all/{self.id}/",json=data)
        self._update_from_old_dict(r.json())

    async def set_icon(self,icon:bytes|str,filetype:str="icon.png"):
        self._is_owner_raise()
        thumbnail,filename = await common.open_tool(icon,filetype)
        form = aiohttp.FormData()
        form.add_field("file",thumbnail,filename=filename)
        await self.ClientSession.post(f"https://scratch.mit.edu/site-api/classrooms/all/{self.id}/",data=form)

    # type: all [username]
    # sort: username
    async def get_privete_activity(
            self, start_page:int=1, end_page:int=1, type:str="all", sort:str="", descending:bool=True
        ) -> AsyncGenerator[activity.Activity, None]:
        self._is_owner_raise()
        add_params = {"descsort" if descending else "ascsort":sort} if sort == "username" else {}
        for i in range(start_page,end_page):
            try:
                r = await common.api_iterative(
                    self.ClientSession,f"https://scratch.mit.edu/site-api/classrooms/activity/{self.id}/{type}/",
                    limit=0,offset=i,is_page=True,add_params=add_params
                )
            except exception.ResponseError:
                return
            for j in r:
                _obj = activity.Activity()
                _obj._update_from_class(self,j)
                yield _obj

    async def create_student_account(
        self,username:str,password:str,birth_day:datetime.date,gender:str,country:str
    ) -> "session.Session":
        common.no_data_checker(self.classtoken)
        data = {
            "classroom_id":self.id,
            "classroom_token": self.classtoken,
            "username": username,
            "password": password,
            "birth_month": birth_day.month,
            "birth_year": birth_day.year,
            "gender": gender,
            "country": country,
            "is_robot": False
        }
        response = await self.ClientSession.post(
            "https://scratch.mit.edu/classes/register_new_student/",data=data,
            cookie={"scratchcsrftoken": 'a'}
        )
        ret = response.json()[0]
        if "username" in ret:
            from . import session
            return await session.session_login(
                str(re.search('"(.*)"', response.headers["Set-Cookie"]).group()).replace("\"","")
            )
        raise exception.BadRequest(response)
    
    async def create_class_studio(self,title:str,description:str):
        self._is_owner_raise()
        common.no_data_checker(self.classtoken)
        r = await self.ClientSession.post(
            "https://scratch.mit.edu/classes/create_classroom_gallery/",
            json={
                "classroom_id":self.id,
                "classroom_token":self.classtoken,
                "title":title,
                "description":description,
                "csrfmiddlewaretoken":"a"
            }
        )
        data = r.json()
        if not data[0].get("succsess"):
            raise exception.BadResponse(r)
        _studio = studio.create_Partial_Studio(data[0].get("gallery_id"))
        _studio.title = title
        _studio.description = description
        _studio.author = self.educator
        return _studio

async def get_classroom(classroom_id:int,*,ClientSession=None) -> Classroom:
    return await base.get_object(ClientSession,classroom_id,Classroom)

async def get_classroom_by_token(class_token:str,*,ClientSession=None) -> Classroom:
    ClientSession = common.create_ClientSession(ClientSession)
    r = (await ClientSession.get(f"https://api.scratch.mit.edu/classtoken/{class_token}")).json()
    _obj = Classroom(ClientSession,r["id"])
    _obj._update_from_dict(r)
    _obj.classtoken = class_token
    return _obj

def create_Partial_classroom(class_id:int,class_token:str|None=None,*,ClientSession:common.ClientSession|None=None,session:"session.Session|None"=None) -> Classroom:
    ClientSession = common.create_ClientSession(ClientSession,session)
    _obj = Classroom(ClientSession,class_id,session)
    _obj.classtoken = class_token
    return _obj