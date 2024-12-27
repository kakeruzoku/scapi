import datetime
from enum import Enum
import random
from typing import AsyncGenerator, Generator, Literal, TypedDict, TYPE_CHECKING, overload
import bs4

from ..others import  common
from ..others import error as exception
from . import base

if TYPE_CHECKING:
    from .session import Session
    from .user import User
    
# & to and
# " " to _
# ' to ""
class ForumCategoryType(Enum):
    unknown = 0
    #Welcome to Scratch
    Announcements = 5
    New_Scratchers = 6
    #Making Scratch Projects
    Help_with_Scripts = 7
    Show_and_Tell = 8
    Project_Ideas = 9
    Collaboration = 10
    Requests = 11
    Project_Save_and_Level_Codes = 60
    #About Scratch
    Questions_about_Scratch = 4
    Suggestions = 1
    Bugs_and_Glitches = 3
    Advanced_Topics = 31
    Connecting_to_the_Physical_World = 32
    Developing_Scratch_Extensions = 48
    Open_Source_Projects = 49
    #Interests Beyond Scratch
    Things_Im_Making_and_Creating = 29
    Things_Im_Reading_and_Playing = 30
    #Scratch Around the World
    Africa = 55
    Bahasa_Indonesia = 36
    Català = 33
    Deutsch = 13
    Ελληνικά = 26
    Español = 14
    فارسی = 59
    Français = 15
    עברית = 22
    한국어 = 23
    Italiano = 21
    Nederlands = 19
    日本語 = 18
    Norsk = 24
    Polski = 17
    Português = 20
    Pусский = 27
    Türkçe = 25
    中文 = 16
    Other_Languages = 34
    Translating_Scratch = 28

    @classmethod
    def value_of(cls, target_value:int) -> "ForumCategoryType":
        for e in ForumCategoryType:
            if e.value == target_value:
                return e
        return ForumCategoryType.unknown


class ForumTopic(base._BaseSiteAPI):
    raise_class = exception.ForumTopicNotFound
    id_name = "id"

    def __init__(
        self,
        ClientSession:common.ClientSession,
        id:int,
        scratch_session:"Session|None"=None,
        **entries
    ):
        super().__init__("get",f"https://scratch.mit.edu/discuss/topic/{id}/",ClientSession,scratch_session)

        self._session = None
        self.id:int = common.try_int(id)
        self.title:str = None
        self.post_count:int|None = None
        self.is_sticky:bool|None = None
        self.is_closed:bool|None = None
        self.view_count:int|None = None
        self.category:ForumCategoryType = ForumCategoryType.unknown
        self.last_update:str|None = None

        self._post_count:int|None = None
        self.last_page:int = 0

    async def update(self):
        self._update_from_dict((await self.ClientSession.get(self.update_url)).text)

    def __str__(self) -> str: return f"<ForumTopic id:{self.id} title:{self.title} category:{self.category} Session:{self.Session}>"
    def __int__(self) -> int: return self.id
    def __eq__(self,value) -> bool: return isinstance(value,User) and self.id == value.id
    def __lt__(self,value) -> bool: return isinstance(value,User) and self.id < value.id
    def __ne__(self,value) -> bool: return isinstance(value,User) and self.id > value.id
    def __le__(self,value) -> bool: return isinstance(value,User) and self.id <= value.id
    def __ge__(self,value) -> bool: return isinstance(value,User) and self.id >= value.id

    def _update_from_dict(self, data:str):
        soup = bs4.BeautifulSoup(data, "html.parser")
        self.title = soup.find("title").text[:-18]
        self.last_page = int(soup.find_all("a",{"class":"page"})[-1].text)
        self.category = ForumCategoryType.value_of(common.split_int(str(soup.find_all("a",{"href":"/discuss/"})[1].next_element.next_element.next_element),"/discuss/","/"))

    def get_reply_count(self):
        pass

async def get_topic(topic_id:int,*,ClientSession=None) -> ForumTopic:
    ClientSession = common.create_ClientSession(ClientSession)
    return await base.get_object(ClientSession,topic_id,ForumTopic)

async def get_topic_list(category:ForumCategoryType,start_page=1,end_page=1,*,ClientSession=None) -> AsyncGenerator[ForumTopic, None]:
    if category == ForumCategoryType.unknown: raise ValueError
    ClientSession = common.create_ClientSession(ClientSession)
    for page in range(start_page,end_page+1):
        html = (await ClientSession.get(f"https://scratch.mit.edu/discuss/{category.value}",params={"page":page})).text
        soup = bs4.BeautifulSoup(html, "html.parser")
        topics = soup.find_all('tr')[1:]
        for topic in topics:
            topic_text = str(topic)
            if topic.find("td",{"class":"djangobbcon1"}) is not None: return
            if '<div class="forumicon">' in topic_text: isopen, issticky = True,False
            if '<div class="iclosed">' in topic_text: isopen, issticky = False,False
            if '<div class="isticky">' in topic_text: isopen, issticky = True,True
            if '<div class="isticky iclosed">' in topic_text: isopen, issticky = False,True
            _titles = topic.find("a")
            id = common.split_int(_titles["href"],"topic/","/")
            _obj = ForumTopic(ClientSession,id)
            _obj.title = _titles.text
            try:
                _obj._post_count = int(topic.find("td",{"class":"tc2"}).text)+1
                _obj.view_count = int(topic.find("td",{"class":"tc3"}).text)
                _obj.last_update = str(topic.find("td",{"class":"tcr"}).find("a").text)
                _obj.last_page = (_obj._post_count+20)//20
            except Exception:
                pass
            _obj.category = category
            _obj.is_closed, _obj.is_sticky = (not isopen), issticky
            yield _obj


def create_Partial_ForumTopic(Topic_id:int|None=None,*,ClientSession:common.ClientSession|None=None,session:"Session|None"=None) -> ForumTopic:
    ClientSession = common.create_ClientSession(ClientSession)
    return ForumTopic(ClientSession,Topic_id,session)
