import datetime
import re
from typing import AsyncGenerator, Literal, TYPE_CHECKING

import bs4

from ..others import  common
from ..others import error as exception
from . import base,user,studio

if TYPE_CHECKING:
    from . import session

class Classroom(base._BaseSiteAPI):
    raise_class = exception.ClassroomNotFound
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
        
    def _update_from_dict(self, data:dict):
        self.title = data.get("title",self.title)
        self._created = data.get("date_start",self._created)
        self.created = common.to_dt(self._created,self.created)
        _author:dict = data.get("educator",{})
        self.educator = user.User(self.ClientSession,_author.get("username",None),self.Session)
        self.educator._update_from_dict(_author)

    async def studios(self, *, start_page=1, end_page=1) -> AsyncGenerator[studio.Studio, None]:
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
                _title = _project.find("span",{"class":"title"})
                _obj = studio.Studio(self.ClientSession,id,self.Session)
                _obj.author_id = self.educator.id
                _obj.title = common.split(str(_title),f"/\">","</a>").strip()
                yield _obj
    
    async def studio_count(self) -> int:
        return await base.get_count(self.ClientSession,f"https://scratch.mit.edu/classes/{self.id}/studios/","Class Studios (",")")

    async def students(self, *, start_page=1, end_page=1) -> AsyncGenerator[user.User, None]:
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

    async def create_student_account(
        self,username:str,password:str,birth_day:datetime.date,gender:str,country:str
    ) -> "session.Session":
        if self.classtoken is None: raise exception.NoDataError
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
        raise exception.BadRequest(response.status_code,response)
    
async def get_classroom(classroom_id:int,*,ClientSession=None) -> Classroom:
    ClientSession = common.create_ClientSession(ClientSession)
    return await base.get_object(ClientSession,classroom_id,Classroom)

async def get_classroom_by_token(class_token:str,*,ClientSession=None) -> Classroom:
    ClientSession = common.create_ClientSession(ClientSession)
    r = (await ClientSession.get(f"https://api.scratch.mit.edu/classtoken/{class_token}")).json()
    _obj = Classroom(ClientSession,r["id"])
    _obj._update_from_dict(r)
    _obj.classtoken = class_token
    return _obj

def create_Partial_classroom(class_id:int,class_token:str|None=None,*,ClientSession:common.ClientSession|None=None,session:"session.Session|None"=None) -> Classroom:
    ClientSession = common.create_ClientSession(ClientSession)
    _obj = Classroom(ClientSession,class_id,session)
    _obj.classtoken = class_token
    return _obj