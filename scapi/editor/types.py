from typing import Any, Literal, TypeVarTuple, TypedDict, NotRequired

# TODO 順番関係あるやつをTlistで表記

Ts = TypeVarTuple('Ts')
Tlist = tuple[*Ts]|list[Any] 

MonitorMode = Literal["default","large","slider"]

VarType = str|int|float|bool|None

class SB3MonitorBase(TypedDict):
    id:str
    opcode:str
    params:dict[str,str]
    spriteName:str|None
    visible:bool
    x:int
    y:int

class SB3NormalMonitor(SB3MonitorBase):
    mode:MonitorMode
    height:Literal[0]
    isDiscrete:bool
    sliderMax:int
    sliderMin:int
    value:VarType
    width:Literal[0]

class SB3ListMonitor(SB3MonitorBase):
    mode:Literal["list"]
    height:int
    value:list[VarType]
    width:int

class SB3Asset(TypedDict):
    assetId:str
    md5ext:str
    name:str

class SB3Costume(SB3Asset):
    bitmapResolution:NotRequired[int]
    dataFormat:Literal["png", "jpg", "jpeg", "svg"]
    rotationCenterX:float
    rotationCenterY:float

class SB3Sound(SB3Asset):
    dataFormat:Literal["wav", "mp3"]
    format:str
    rate:int
    sampleCount:int

SB3Variable = Tlist[str,VarType]|Tlist[str,VarType,Literal[True]]

SB3List = Tlist[str,list[VarType]]

class SB3SpriteBase(TypedDict):
    blocks:dict[str,dict]
    broadcasts:dict[str,str]
    comments:dict[str,dict]
    costumes:list[SB3Costume]
    currentCostume:int #0始まり
    lists:dict[str,SB3List]
    name:str
    sounds:list[SB3Sound]
    variables:dict[str,SB3Variable]
    volume:int

RotationStyleText = str #TODO

class Sprite3Sprite(SB3SpriteBase):
    direction:int
    draggable:bool
    isStage:Literal[False]
    rotationStyle:RotationStyleText
    size:int
    visible:bool
    x:float
    y:float

class SB3Sprite(Sprite3Sprite):
    layerOrder:int

VideoStateText = str #TODO

class SB3Stage(SB3SpriteBase):
    isStage:Literal[True]
    layerOrder:Literal[0]
    tempo:int
    textToSpeechLanguage:str
    videoState:VideoStateText
    videoTransparency:int

class SB3Meta(TypedDict):
    agent:str
    semver:str
    vm:str

class SB3Project(TypedDict):
    extensions:list[str]
    meta:SB3Meta
    monitors:list
    targets:list[SB3Sprite|SB3Stage]