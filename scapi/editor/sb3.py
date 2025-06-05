from ..others import common
from . import project
from typing import TypedDict

class _sb3_monitor(TypedDict):
    pass

class _sb3_meta(TypedDict):
    agent:str
    semver:str
    vm:str

class _sb3_json(TypedDict):
    extensions:list[str]
    meta:_sb3_meta
    monitors:list[_sb3_monitor]



def load_from_json(obj:_sb3_json):
    p = project.ScratchProject()
    info = obj.get("meta")
    p.info.useragent = info.get("agent")