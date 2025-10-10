from typing import TYPE_CHECKING, Any, Final, Literal, Self, Unpack, TypedDict

from .types import SB3Stage,SB3Sprite,SB3SpriteBase,RotationStyleText,VideoStateText
from .variable import Variable

if TYPE_CHECKING:
    from .project import Project

class SpriteBaseIn(TypedDict,total=False):
    current_costume:int

class SpriteIn(SpriteBaseIn,total=False):
    layer_order:int
    direction:int
    draggable:bool
    rotationStyle:RotationStyleText
    size:int
    visible:bool
    volume:int
    x:int
    y:int

class StageIn(SpriteBaseIn,total=False):
    tempo:int
    t2t_language:str
    video_state:VideoStateText
    video_transparency:int
    volume:int

class SpriteBase:
    layer_order:int|None
    def __init__(self,name:str,*,project:"Project|None"=None,**kwargs:Unpack[SpriteBaseIn]):
        self.name:str = name
        self._project:"Project|None" = project

        self.current_costume:int = kwargs.get("current_costume") or 1
        self.variables:dict[str,Variable] = {}

    def _setup_variables(self,variables:list[Variable]):
        self.variables = {var.name:var for var in variables}

    def _add_to_project(self,project:"Project"):
        if self._project is not None:
            raise ValueError()
        self._project = project #TODO layer_order処理

    def to_sb3(self) -> SB3SpriteBase:
        return {
            "blocks":{},
            "broadcasts":{},
            "comments":{},
            "costumes":[],
            "currentCostume":self.current_costume,
            "lists":{},
            "name":self.name,
            "sounds":[],
            "variables":{},
        }

class Sprite(SpriteBase):
    is_stage:Final[Literal[False]] = False
    def __init__(self,name:str,*,project:"Project|None"=None,**kwargs:Unpack[SpriteIn]):
        super().__init__(name,project=project,**kwargs)
        self.layer_order:int|None = kwargs.get("layer_order")
        self.direction:int = kwargs.get("direction",90)
        self.draggable:bool = kwargs.get("draggable",False)
        self.rotation_style:RotationStyleText = kwargs.get("rotationStyle","all around")
        self.size:int = kwargs.get("size",100)
        self.visible:bool = kwargs.get("visible",True)
        self.volume:int = kwargs.get("volume",100)
        self.x:int = kwargs.get("x",0)
        self.y:int = kwargs.get("y",0)

    @classmethod
    def from_sb3(cls, data:SB3Sprite, project:"Project|None"=None) -> Self:
        sprite = cls(
            data["name"],
            project=project,
            current_costume=data["currentCostume"] + 1,
            layer_order=data["layerOrder"],
            direction=data["direction"],
            draggable=data["draggable"],
            rotationStyle=data["rotationStyle"],
            size=data["size"],
            visible=data["visible"],
            volume=data["volume"],
            x=data["x"],
            y=data["y"],
        )
        sprite._setup_variables([Variable.from_sb3(k,v,sprite) for k,v in data["variables"].items()])
        return sprite
    
    def to_sb3(self) -> SB3Sprite:
        base = super().to_sb3()
        return base|{
            "direction":self.direction,
            "draggable":self.draggable,
            "isStage":False,
            "layerOrder":self.layer_order or 0, #TODO
            "rotationStyle":self.rotation_style,
            "size":self.size,
            "visible":self.visible,
            "volume":self.volume,
            "x":self.x,
            "y":self.y
        } # pyright: ignore[reportReturnType]
    
class Stage(SpriteBase):
    is_stage:Final[Literal[True]] = True
    def __init__(self, project:"Project|None"=None, **kwargs:Unpack[StageIn]):
        super().__init__(
            "Stage",
            project=project,
            **kwargs
        )
        self.layer_order = 0
        self.tempo:int = kwargs.get("tempo",60)
        self.t2t_language:str = kwargs.get("t2t_language","en")
        self.video_state:VideoStateText = kwargs.get("video_state","on")
        self.video_transparency:int = kwargs.get("video_transparency",50)
        self.volume:int = kwargs.get("volume",100)

    @classmethod
    def from_sb3(cls, data:SB3Stage, project:"Project|None"=None) -> Self:
        stage = cls(
            project=project,
            current_costume=data["currentCostume"] + 1,
            tempo=data["tempo"],
            t2t_language=data["textToSpeechLanguage"],
            video_state=data["videoState"],
            video_transparency=data["videoTransparency"],
            volume=data["volume"],
        )
        stage._setup_variables([Variable.from_sb3(k,v,stage) for k,v in data["variables"].items()])
        return stage
    
    def to_sb3(self) -> SB3Stage:
        base = super().to_sb3()
        return base|{
            "isStage":True,
            "layerOrder":0, #TODO
            "tempo":self.tempo,
            "textToSpeechLanguage":self.t2t_language,
            "videoState":self.video_state,
            "videoTransparency":self.video_transparency,
            "volume":self.volume
        } # pyright: ignore[reportReturnType]
    
AnySprite = Sprite|Stage