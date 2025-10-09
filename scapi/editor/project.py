from typing import Any,Unpack,TypedDict
from .common import Base
from .types import SB3Project
from ..utils.common import __version__
from .info import Info

class ProjectIn(TypedDict,total=False):
    info:Info

class Project(Base):
    def __init__(self,**kwargs:Unpack[ProjectIn]):
        self.info:Info = kwargs.get("info") or Info()

    @classmethod
    def from_sb3(cls, data:SB3Project):
        project = cls()
        return project
    
    def to_sb3(self) -> SB3Project:
        return {
            "meta":self.info.to_sb3(),
            "extensions":[],
            "monitors":[],
            "targets":[]
        }