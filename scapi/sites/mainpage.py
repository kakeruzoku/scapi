import datetime
import random
from typing import AsyncGenerator, Generator, Literal, TypedDict, TYPE_CHECKING
import warnings

from ..others import common
from ..others import error as exception
from . import base,project,comment,activity,studio

import bs4

if TYPE_CHECKING:
    from . import session

class ScratchNews(base._BaseSiteAPI):
    raise_class = exception.ObjectNotFound
    id_name = "id"

    def __str__(self):
        return f"<ScratchNews id:{self.id} title:{self.title} url:{self.url}>"
    
    def __init__(
        self,
        ClientSession:common.ClientSession,
        id:int,
        scratch_session:"session.Session|None"=None,
        **entries
    ):
        
        super().__init__("get",f"",ClientSession,scratch_session)

        self.id:int = common.try_int(id)
        self._timestamp:str = None
        self.timestamp:datetime.datetime = None
        self.url:str = None
        self.image_url:str = None
        self.title:str = None
        self.content:str = None

    async def update():
        warnings.warn("ScratchNews can't update")

    async def _update_from_dict(self, data:dict):
        self.id = data.get("id",self.id)
        self._timestamp = data.get("stamp",self._timestamp)
        self.timestamp = common.to_dt(self._timestamp,self.timestamp)
        self.title = data.get("headline",self.title)
        self.url = data.get("url",self.url)
        self.image_url = data.get("image",self.image_url)
        self.content = data.get("copy",self.content)

def get_scratchnews(limit=40, offset=0, clientsession:common.ClientSession|None=None) -> AsyncGenerator[ScratchNews,None]:
        clientsession = common.create_ClientSession(clientsession)
        return base.get_object_iterator(
            clientsession,"api.scratch.mit.edu/news",None,ScratchNews,None,
            limit=limit,offset=offset
        )

class community_featured_response(TypedDict):
    featured_projects:list[project.Project]
    featured_studios:list[studio.Studio]
    most_loved_projects:list[project.Project]
    most_remixed_projects:list[project.Project]
    newest_projects:list[project.Project]
    design_studio_projects:list[project.Project]
    design_studio:studio.Studio


async def community_featured(clientsession:common.ClientSession|None=None,session:"session.Session|None"=None) -> community_featured_response:
    clientsession = common.create_ClientSession(clientsession)
    resp:dict[str,list[dict]] = (await clientsession.get("https://api.scratch.mit.edu/proxy/featured")).json()
    r:community_featured_response = {}
    cfp = []
    for i in resp.get("community_featured_projects",[]):
        p = project.create_Partial_Project(i.get("id"),i.get("creator"),ClientSession=clientsession,session=session)
        p.title = i.get("title"); p.loves = i.get("love_count")
        cfp.append(p)
    r["featured_projects"] = cfp
    cfs = []
    for i in resp.get("community_featured_studios",[]):
        s = studio.create_Partial_Studio(i.get("id"),ClientSession=clientsession,session=session)
        s.title = i.get("title")
        cfs.append(s)
    r["featured_studios"] = cfs
    cml = []
    for i in resp.get("community_most_loved_projects",[]):
        p = project.create_Partial_Project(i.get("id"),i.get("creator"),ClientSession=clientsession,session=session)
        p.title = i.get("title"); p.loves = i.get("love_count")
        cml.append(p)
    r["most_loved_projects"] = cml
    cmr = []
    for i in resp.get("community_most_remixed_projects",[]):
        p = project.create_Partial_Project(i.get("id"),i.get("creator"),ClientSession=clientsession,session=session)
        p.title = i.get("title"); p.loves = i.get("love_count"); p.remix_count = i.get("remixers_count")
        cmr.append(p)
    r["most_remixed_projects"] = cmr
    cnp = []
    for i in resp.get("community_newest_projects",[]):
        p = project.create_Partial_Project(i.get("id"),i.get("creator"),ClientSession=clientsession,session=session)
        p.title = i.get("title"); p.loves = i.get("love_count")
        cnp.append(p)
    r["newest_projects"] = cnp
    sds = []
    for i in resp.get("scratch_design_studio",[]):
        p = project.create_Partial_Project(i.get("id"),i.get("creator"),ClientSession=clientsession,session=session)
        p.title = i.get("title"); p.loves = i.get("love_count"); p.remix_count = i.get("remixers_count")
        sds.append(p)
    r["design_studio_projects"] = sds
    s_dict = resp.get("scratch_design_studio",[None])[0]
    if s_dict is None: r["design_studio"] = None
    else:
        s_obj = studio.create_Partial_Studio(s_dict.get("gallery_id"),ClientSession=clientsession,session=session)
        s_obj.title = s_dict.get("gallery_title")
        r["design_studio"] = s_obj
    return r
