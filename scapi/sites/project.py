import asyncio
import datetime
import json
import os
import random
from typing import AsyncGenerator, TYPE_CHECKING, TypedDict
import warnings
import zipfile
import aiofiles


from ..others import common
from ..others import error as exception
from . import base,activity,comment

if TYPE_CHECKING:
    from .session import Session
    from .user import User
    from .studio import Studio
    from ..event.comment import CommentEvent
    from ..cloud import cloud,cloud_event

class Project(base._BaseSiteAPI):
    id_name = "id"

    def __repr__(self):
        return f"<Project id:{self.id} title:{self.title} Session:{self.Session}>"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        id:int,
        scratch_session:"Session|None"=None,
        **entries
    ) -> None:
        super().__init__("get",f"https://api.scratch.mit.edu/projects/{id}",ClientSession,scratch_session)
        
        self.id:int = common.try_int(id)
        self.project_token:str = None
        
        self.author:"User" = None
        self.title:str = None
        self.instructions:str = None
        self.notes:str = None

        self.loves:int = None
        self.favorites:int = None
        self.remix_count:int = None
        self.views:int = None

        self._created:str = None
        self._shared:str = None
        self._modified:str = None
        self.created:datetime.datetime = None
        self.shared:datetime.datetime = None
        self.modified:datetime.datetime = None

        self.comments_allowed:bool = None
        self.remix_parent:int|None = None
        self.remix_root:int|None = None

        self.comment_count:int|None = None

    def _update_from_dict(self, data:dict) -> None:
        from .user import User
        _author:dict = data.get("author",{})
        self.author = User(self.ClientSession,_author.get("username",None),self.Session)
        self.author._update_from_dict(_author)
        
        self.comments_allowed = data.get("comments_allowed",self.comments_allowed)
        self.instructions = data.get("instructions",self.instructions)
        self.notes = data.get("description",self.notes)
        self.title:str = data.get("title")
        self.project_token:str = data.get("project_token")

        _history:dict = data.get("history",{})
        self._add_datetime("created",_history.get("created"))
        self._add_datetime("modified",_history.get("modified"))
        self._add_datetime("shared",_history.get("shared"))

        _remix:dict = data.get("remix",{})
        self.remix_parent = _remix.get("parent",self.remix_parent)
        self.remix_root = _remix.get("root",self.remix_root)

        _stats:dict = data.get("stats",{})
        self.favorites = _stats.get("favorites",self.favorites)
        self.loves = _stats.get("loves",self.loves)
        self.remix_count = _stats.get("remixes",self.remix_count)
        self.views = _stats.get("views",self.views)

        self.comment_count = _stats.get("comments",self.comment_count) #only mystuff

    def _update_from_old_dict(self, fields:dict):
        from . import user
        self.views = fields.get("view_count",self.views)
        self.favorites = fields.get("favorite_count",self.favorites)
        self.remix_count = fields.get("remixers_count",self.remix_count)
        _author:dict = fields.get("creator",{})
        self.author = user.User(self.ClientSession,_author.get("username",self.Session.username),self.Session)
        self.author.id = _author.get("pk",self.Session.status.id)
        self.author.scratchteam = _author.get("admin",self.Session.status.admin)

        self.title = fields.get("title",self.title)

        self._add_datetime("created",fields.get("datetime_created"))
        self._add_datetime("modified",fields.get("datetime_modified"))
        self._add_datetime("shared",fields.get("datetime_shared"))

        self.loves = fields.get("love_count",self.loves)
        self.comment_count = fields.get("commenters_count",self.comment_count)

    def _update_from_mystuff(self, data:dict):
        self._update_from_old_dict(data.get("fields"))

    @property
    def _is_owner(self) -> bool:
        from .session import Session
        common.no_data_checker(self.author)
        common.no_data_checker(self.author.username)
        if isinstance(self.Session,Session):
            if self.Session.username == self.author.username:
                return True
        return False
    
    @property
    def thumbnail_url(self) -> str:
        return f"https://cdn2.scratch.mit.edu/get_image/project/{self.id}_480x360.png"
    
    @property
    def url(self) -> str:
        return f"https://scratch.mit.edu/projects/{self.id}/"
    
    def _is_owner_raise(self) -> None:
        if self.check and not self._is_owner:
            raise exception.NoPermission
    
    def __int__(self) -> int: return self.id
    def __eq__(self,value) -> bool: return isinstance(value,Project) and self.id == value.id
    def __ne__(self,value) -> bool: return isinstance(value,Project) and self.id != value.id
    def __lt__(self,value) -> bool: return isinstance(value,Project) and self.id < value.id
    def __gt__(self,value) -> bool: return isinstance(value,Project) and self.id > value.id
    def __le__(self,value) -> bool: return isinstance(value,Project) and self.id <= value.id
    def __ge__(self,value) -> bool: return isinstance(value,Project) and self.id >= value.id

    def remixes(self, *, limit=40, offset=0) -> AsyncGenerator["Project",None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/projects/{self.id}/remixes",
            None,Project,self.Session,
            limit=limit,offset=offset
        )
    
    async def create_remix(self,title:str|None=None) -> "Project":
        self.has_session_raise()
        try:
            project_json = await self.load_json()
        except:
            project_json = common.empty_project_json
        if title is None:
            if self.title is None:
                title = f"{self.id} remix"
            else:
                title = f"{self.title} remix"

        return await self.Session.create_project(title,project_json,self.id)

    async def load_json(self,update:bool=True) -> common.json_resp:
        try:
            if update or self.project_token is None:
                await self.update()
            return (await self.ClientSession.get(
                f"https://projects.scratch.mit.edu/{self.id}?token={self.project_token}"
            )).json()
        except Exception as e:
            raise exception.ObjectNotFound(Project,e)
        
    async def download(self,save_path,filename:str|None=None,download_asset:bool=True,log:bool=False) -> str:
        if filename is None:
            filename = f"{self.id}_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.sb3"
        if not filename.endswith(".sb3"):
            filename = filename + ".sb3"
        zip_directory = os.path.join(save_path,f"_{self.id}_{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}_download").replace("\\","/")
        try:
            os.makedirs(zip_directory)
            if log: print(f'Created folder:{zip_directory}')
        except Exception:
            raise ValueError(f'Did not create folder:{zip_directory}')
        project_json = await self.load_json()
        if log: print(f'download:project.json')
        asset_list:list[str] = []
        if download_asset:
            for i in project_json["targets"]:
                for j in i["costumes"]:
                    asset_list.append(j['md5ext'])
                for j in i["sounds"]:
                    asset_list.append(j['md5ext'])
        asset_list = list(set(asset_list))
        
        async def assetdownloader(clientsession:common.ClientSession,filepath:str,asset_id:str):
            r = await clientsession.get(f"https://assets.scratch.mit.edu/internalapi/asset/{asset_id}/get/")
            if log: print(f'download:{asset_id}')
            async with aiofiles.open(os.path.join(filepath,asset_id),"bw") as f:
                await f.write(r.data)
                if log: print(f'wrote:{asset_id}')

        async def saveproject(filepath:str,asset_id:str):
            async with aiofiles.open(os.path.join(filepath,asset_id),"w",encoding="utf-8") as f:
                await f.write(json.dumps(project_json, separators=(',', ':'), ensure_ascii=False))
                if log: print(f'wrote:project.json')
        
        tasks = [assetdownloader(self.ClientSession,zip_directory,asset_id) for asset_id in asset_list] +\
                [saveproject(zip_directory,"project.json")]
        await asyncio.gather(*tasks)
        with zipfile.ZipFile(os.path.join(save_path,filename), "a", zipfile.ZIP_STORED) as f:
            for asset_id in asset_list:
                f.write(os.path.join(zip_directory,asset_id),asset_id)
                if log: print(f'ziped:{asset_id}')
            f.write(os.path.join(zip_directory,"project.json"),"project.json")
            if log: print(f'ziped:project.json')
        for asset_id in asset_list:
            os.remove(os.path.join(zip_directory,asset_id))
            if log: print(f'removed:{asset_id}')
        os.remove(os.path.join(zip_directory,"project.json"))
        if log: print(f'removed:project.json')
        try:
            os.rmdir(zip_directory)
            if log: print(f'removed:{zip_directory}')
        except:
            pass
        if log: print("success:"+os.path.join(save_path,filename).replace("\\","/"))
        return os.path.join(save_path,filename).replace("\\","/")



        


    async def love(self,love:bool=True) -> bool:
        self.has_session_raise()
        if love:
            r = (await self.ClientSession.post(f"https://api.scratch.mit.edu/projects/{self.id}/loves/user/{self.Session.username}")).json()
        else:
            r = (await self.ClientSession.delete(f"https://api.scratch.mit.edu/projects/{self.id}/loves/user/{self.Session.username}")).json()
        return r["statusChanged"]
    
    async def favorite(self,favorite:bool=True) -> bool:
        self.has_session_raise()
        if favorite:
            r = (await self.ClientSession.post(f"https://api.scratch.mit.edu/projects/{self.id}/favorites/user/{self.Session.username}")).json()
        else:
            r = (await self.ClientSession.delete(f"https://api.scratch.mit.edu/projects/{self.id}/favorites/user/{self.Session.username}")).json()
        return r["statusChanged"]
    
    async def view(self) -> bool:
        common.no_data_checker(self.author)
        common.no_data_checker(self.author.username)
        try:
            await self.ClientSession.post(f"https://api.scratch.mit.edu/users/{self.author.username}/projects/{self.id}/views/")
        except exception.TooManyRequests:
            return False
        return True
    
    async def edit(
            self,
            comment_allowed:bool|None=None,
            title:str|None=None,
            instructions:str|None=None,
            notes:str|None=None,
        ):
        data = {}
        if comment_allowed is not None: data["comments_allowed"] = comment_allowed
        if title is not None: data["title"] = title
        if instructions is not None: data["instructions"] = instructions
        if notes is not None: data["description"] = notes
        self._is_owner_raise()
        r = await self.ClientSession.put(f"https://api.scratch.mit.edu/projects/{self.id}",json=data)
        self._update_from_dict(r.json())

    async def old_edit(
            self,
            title:str|None=None,
            share:bool|None=None,
            trash:bool|None=None,
        ):
        data = {}
        if share is not None: data["isPublished"] = share
        if title is not None: data["title"] = title
        if trash is not None: data["visibility"] = "trshbyusr" if trash else "visible"
        self._is_owner_raise()
        await self.ClientSession.put(f"https://scratch.mit.edu/site-api/projects/all/{self.id}/",json=data)
        self.title = title or self.title

    async def set_thumbnail(self,thumbnail:bytes|str):
        self._is_owner_raise()
        thumbnail,filename = await common.open_tool(thumbnail,"png")
        await self.ClientSession.post(
            f"https://scratch.mit.edu/internalapi/project/thumbnail/{self.id}/set/",
            data=thumbnail,
        )

    async def set_json(self,data:dict|str):
        self._is_owner_raise()
        if isinstance(data,str):
            data = json.loads(data)
        r = (await self.ClientSession.put(
            f"https://projects.scratch.mit.edu/{self.id}",
            json=data,
        ))
        jsons = r.json()
        if not ("status" in jsons and jsons["status"] == "ok"):
            raise exception.BadRequest(r)
        
        
    def studios(self, *, limit=40, offset=0) -> AsyncGenerator["Studio",None]:
        common.no_data_checker(self.author)
        common.no_data_checker(self.author.username)
        from .studio import Studio
        return base.get_object_iterator(
            self.ClientSession,f"https://api.scratch.mit.edu/users/{self.author.username}/projects/{self.id}/studios",
            None,Studio,self.Session,
            limit=limit,offset=offset
        )
    
    async def get_comment_by_id(self,id:int,is_old:bool|None=None) -> comment.Comment:
        if is_old is None:
            is_old = (self.author and self.author.username) is None

        if is_old:
            return await comment._get_comment_old_api_by_id(self,f"https://scratch.mit.edu/site-api/comments/project/{self.id}",id)
        else:
            common.no_data_checker(self.author)
            common.no_data_checker(self.author.username)
            return await base.get_object(
                self.ClientSession,id,comment.Comment,self.Session,base._comment_get_func,others={"plece":self}
            )

    def get_comments(self, *, limit:int=40, offset:int=0, start_page:int=1, end_page:int=1, is_old:bool|None=None) -> AsyncGenerator[comment.Comment, None]:
        if is_old is None:
            is_old = (self.author and self.author.username) is None

        if is_old:
            return comment._get_comments_old_api(self,f"https://scratch.mit.edu/site-api/comments/project/{self.id}",start_page=start_page,end_page=end_page)
        else:
            common.no_data_checker(self.author)
            common.no_data_checker(self.author.username)
            return base.get_object_iterator(
                self.ClientSession,f"https://api.scratch.mit.edu/users/{self.author.username}/projects/{self.id}/comments",None,comment.Comment,
                limit=limit,offset=offset,add_params={"cachebust":random.randint(0,9999)},
                custom_func=base._comment_iterator_func, others={"plece":self}
            )
    
    async def post_comment(self, content:str, parent:int|comment.Comment|None=None, commentee:"int|User|None"=None, is_old:bool|None=None) -> comment.Comment:
        self.has_session_raise()

        if is_old is None: is_old = False
        if is_old: url = f"https://scratch.mit.edu/site-api/comments/project/{self.id}/add/"
        else: url = f"https://api.scratch.mit.edu/proxy/comments/project/{self.id}/"

        return await comment._post_comment(
            self,url,is_old,content,common.get_id(commentee),common.get_id(parent)
        )
    
    def comment_event(self,interval=30) -> "CommentEvent":
        from ..event.comment import CommentEvent
        return CommentEvent(self,interval)
    
    async def share(self,share:bool=True):
        self._is_owner_raise()
        if share:
            await self.ClientSession.put(f"https://api.scratch.mit.edu/proxy/projects/{self.id}/share/",)
        else:
            await self.ClientSession.put(f"https://api.scratch.mit.edu/proxy/projects/{self.id}/unshare/",)

    class project_visibility(TypedDict):
        projectId:int
        creatorId:int
        deleted:bool
        censored:bool
        censoredByAdmin:bool
        censoredByCommunity:bool
        reshareable:bool
        message:str

    async def visibility(self) -> project_visibility:
        self._is_owner_raise()
        r = (await self.ClientSession.get(f"https://api.scratch.mit.edu/users/{self.Session.username}/projects/{self.id}/visibility")).json()
        return r
    
    async def report(self,category:int,message:str):
        r = await self.ClientSession.post(
            f"https://api.scratch.mit.edu/proxy/projects/{self.id}/report",
            json={
                "notes":message,
                "report_category":str(category),
                "thumbnail":""
            }
        )
        #{"moderation_status": "notreviewed", "success": true} or 空白
        if len(r.text) == 0:
            raise exception.BadResponse(r)
        if not r.json().get("success"):
            raise exception.BadResponse(r)
        return
    
    async def get_remixtree(self) -> "RemixTree":
        _tree = await get_remixtree(self.id,ClientSession=self.ClientSession,session=self.Session)
        _tree.project = self
        return _tree
    
    def get_cloud(self) -> "cloud.ScratchCloud":
        self.has_session_raise()
        return self.Session.get_cloud(self.id)
    
    def get_cloud_logs(self, *, limit:int=100, offset:int=0) -> AsyncGenerator[activity.CloudActivity, None]:
        return base.get_object_iterator(
            self.ClientSession,"https://clouddata.scratch.mit.edu/logs",
            None,activity.CloudActivity,self.Session,
            limit=limit,offset=offset,max_limit=100,add_params={"projectid":self.id},
            custom_func=base._cloud_activity_iterator_func,others={"project_id":self.id}
        )
    
    def cloud_log_event(self,interval:float=1) -> "cloud_event.CloudLogEvent":
        from ..cloud import cloud_event
        obj = cloud_event.CloudLogEvent(self.id,self.ClientSession,interval)
        obj.Session = self.Session
        return obj


class RemixTree(base._BaseSiteAPI): #no data
    id_name = "id"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        id:int,
        scratch_session:"Session|None"=None,
        **entries
    ) -> None:
        super().__init__("get",f"https://scratch.mit.edu/projects/{id}/remixtree/bare/",ClientSession,scratch_session)

        self.id:int = common.try_int(id)
        self.is_root:bool = False
        self._parent:int|None = None
        self._root:int = None
        self.project:Project = create_Partial_Project(self.id,ClientSession=self.ClientSession,session=self.Session)
        self._children:list[int] = []
        self.moderation_status:str = None
        self._ctime:int = None #idk what is ctime
        self.ctime:datetime.datetime = None
        self.is_published:bool = None
        self._all_remixtree:dict[int,"RemixTree"] = None

    def __repr__(self):
        return f"<RemixTree remix_count:{len(self._children)} status:{self.moderation_status} project:{self.project}> session:{self.Session}"

    async def update(self):
        warnings.warn("remixtree can't update")

    def _update_from_dict(self, data:dict):
        from . import user
        self.project.author = user.create_Partial_User(data.get("username"),ClientSession=self.ClientSession,session=self.Session)
        self.moderation_status = data.get("moderation_status",self.moderation_status)

        _ctime = data.get("ctime")
        if isinstance(_ctime,dict):
            self._ctime = _ctime.get("$date",self._ctime)
            self.ctime = common.to_dt_timestamp_1000(self._ctime,self.ctime)
        
        self.project.title = data.get("title",self.project.title)
        self.project.remix_parent = data.get("parent_id",self.project.remix_parent)
        if isinstance(self.project.remix_parent,str):
            self.project.remix_parent = common.try_int(self.project.remix_parent)
        self._parent = self.project.remix_parent
        
        self.project.loves = data.get("love_count",self.project.loves)
        _mtime = data.get("mtime")
        if isinstance(_mtime,dict):
            self.project._modified = _mtime.get("$date",self.project._modified)
            self.project.modified = common.to_dt_timestamp_1000(self.project._modified,self.project.modified)
        
        _datetime_shared = data.get("datetime_shared")
        if isinstance(_datetime_shared,dict):
            self.project._shared = _datetime_shared.get("$date",self.project._shared)
            self.project.shared = common.to_dt_timestamp_1000(self.project._shared,self.project.shared)
        self.project.favorites = data.get("favorite_count",self.project.favorites)
        _children = data.get("children",self._children)
        self._children = []
        self.is_published = data.get("is_published")
        for i in _children:
            self._children.append(int(i))

    @property
    def parent(self) -> "RemixTree|None":
        if self._parent is None:
            return None
        return self._all_remixtree.get(self._parent)
    
    @property
    def children(self) -> list["RemixTree"]:
        r = []
        for id in self._children:
            rt = self._all_remixtree.get(id)
            if rt is None: continue
            r.append(rt)
        return r
    
    @property
    def root(self) -> "RemixTree":
        return self._all_remixtree.get(self._root)

    @property
    def all_remixtree(self)  -> dict[int,"RemixTree"]:
        return self._all_remixtree.copy()

async def get_remixtree(project_id:int,*,ClientSession:common.ClientSession|None=None,session:"Session|None"=None) -> RemixTree:
    ClientSession = common.create_ClientSession(ClientSession,session)
    r = await ClientSession.get(f"https://scratch.mit.edu/projects/{project_id}/remixtree/bare/")
    if r.text == "no data" or r.text == "not visible":
        raise exception.ObjectNotFound(RemixTree,ValueError)
    rtl:dict[int,RemixTree] = {}
    j = r.json()
    root_id = j["root_id"]
    del j["root_id"]
    for k,v in j.items():
        _obj = RemixTree(ClientSession,k,session)
        _obj._update_from_dict(v)
        _obj.project.remix_root = int(root_id)
        rtl[_obj.id] = _obj
        if k == root_id:
            _root = _obj
            _root.is_root = True
        if int(project_id) == _obj.id:
            _return = _obj
    for i in rtl.values():
        i._root = _root.id
        i._all_remixtree = rtl
    return _return

async def get_project(project_id:int,*,ClientSession=None) -> Project:
    return await base.get_object(ClientSession,project_id,Project)

def create_Partial_Project(project_id:int,author:"User|None"=None,*,ClientSession:common.ClientSession|None=None,session:"Session|None"=None) -> Project:
    ClientSession = common.create_ClientSession(ClientSession,session)
    _project = Project(ClientSession,project_id,session)
    if author is not None:
        _project.author = author
    return _project


def explore_projects(*, query:str="*", mode:str="trending", language:str="en", limit:int=40, offset:int=0,ClientSession:common.ClientSession|None=None) -> AsyncGenerator["Project",None]:
    return base.get_object_iterator(
        ClientSession, "https://api.scratch.mit.edu/explore/projects",
        None,Project,limit=limit,offset=offset,
        add_params={"language":language,"mode":mode,"q":query}
    )

def search_projects(query:str, *, mode:str="trending", language:str="en", limit:int=40, offset:int=0,ClientSession:common.ClientSession|None=None) -> AsyncGenerator["Project",None]:
    return base.get_object_iterator(
        ClientSession, "https://api.scratch.mit.edu/search/projects",
        None,Project,limit=limit,offset=offset,
        add_params={"language":language,"mode":mode,"q":query}
    )