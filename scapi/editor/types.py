from typing import TypedDict

class SB3Meta(TypedDict):
    agent:str
    semver:str
    vm:str

class SB3Project(TypedDict):
    extensions:list[str]
    meta:SB3Meta
    monitors:list
    targets:list