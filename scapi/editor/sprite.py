from typing import TYPE_CHECKING, Any, Final, Literal, Self, Unpack, TypedDict

from .types import SB3Stage,SB3Sprite,SB3SpriteBase,RotationStyleText,VideoStateText,VarType,Sprite3Sprite
from .variable import Variable,List,Broadcast
from .asset import Costume,Sound

if TYPE_CHECKING:
    from .project import ProjectEditor


class SpriteBase:
    current_costume:int
    volume:int
    
    def __init__(self,name:str,_project:"ProjectEditor|None"=None):
        self.name:str = name
        self._project:"ProjectEditor|None" = _project
        self._variables:dict[str,Variable] = {}
        self._lists:dict[str,List] = {}
        self._broadcasts:dict[str,Broadcast] = {}
        self.costumes:list[Costume] = []
        self.sounds:list[Sound] = []

    def _init(self):
        self.current_costume = 1
        self.volume = 100

    def _setup_vlb(self,variables:list[Variable],lists:list[List],broadcasts:list[Broadcast]):
        self._variables = {var.name:var for var in variables}
        self._lists = {l.name:l for l in lists}
        self._broadcasts = {cast.name:cast for cast in broadcasts}

    def _from_sb3(self,sprite:"AnySprite",data:SB3SpriteBase):
        assert self == sprite
        self.current_costume = data["currentCostume"]
        self.volume = data["volume"]
        self._setup_vlb(
            [Variable.from_sb3(k,v,sprite) for k,v in data["variables"].items()],
            [List.from_sb3(k,v,sprite) for k,v in data["lists"].items()],
            [Broadcast.from_sb3(k,v,sprite) for k,v in data["broadcasts"].items()]
        )
        self.costumes = [Costume.from_sb3(i,sprite) for i in data["costumes"]]
        self.sounds = [Sound.from_sb3(i,sprite) for i in data["sounds"]]

    def to_sb3(self) -> SB3SpriteBase:
        return {
            "blocks":{},
            "broadcasts":{k:v for k,v in [i.to_sb3() for i in self.broadcasts]},
            "comments":{},
            "costumes":[i.to_sb3() for i in self.costumes],
            "currentCostume":self.current_costume,
            "lists":{k:v for k,v in [i.to_sb3() for i in self.lists]},
            "name":self.name,
            "sounds":[i.to_sb3() for i in self.sounds],
            "variables":{k:v for k,v in [i.to_sb3() for i in self.variables]},
            "volume":self.volume
        }
    
    @property
    def project(self) -> "ProjectEditor|None":
        return self._project
    
    @property
    def variables(self) -> list[Variable]:
        return list(self._variables.values())
    
    @property
    def lists(self) -> list[List]:
        return list(self._lists.values())
    
    @property
    def broadcasts(self) -> list[Broadcast]:
        return list(self._broadcasts.values())
    
class Sprite(SpriteBase):
    is_stage:Final[Literal[False]] = False

    layer_order:int|None
    direction:int
    draggable:bool
    rotation_style:RotationStyleText
    size:int
    visible:bool
    volume:int
    x:float
    y:float

    def _init(self):
        self.layer_order = None
        self.direction = 90
        self.draggable = False
        self.rotation_style = "all around"
        self.size = 100
        self.visible = True
        self.volume = 100
        self.x = 0
        self.y = 0

    @classmethod
    def from_sb3(cls, data:SB3Sprite|Sprite3Sprite, project:"ProjectEditor|None"=None) -> Self:
        sprite = cls(data["name"],project)
        sprite._from_sb3(sprite,data)

        sprite.layer_order = data.get("layerOrder")
        sprite.direction = data["direction"]
        sprite.draggable = data["draggable"]
        sprite.rotation_style = data["rotationStyle"]
        sprite.size = data["size"]
        sprite.visible = data["visible"]
        sprite.volume = data["volume"]
        sprite.x = data["x"]
        sprite.y = data["y"]
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
            "x":self.x,
            "y":self.y
        } # pyright: ignore[reportReturnType]
    
class Stage(SpriteBase):
    is_stage:Final[Literal[True]] = True

    tempo:int
    t2t_language:str
    video_state:VideoStateText
    video_transparency:int

    def __init__(self,_project:"ProjectEditor"):
        super().__init__("Stage",_project)

    def _init(self):
        self.tempo = 60
        self.t2t_language = "en"
        self.video_state = "on"
        self.video_transparency = 50

    @classmethod
    def from_sb3(cls, data:SB3Stage, project:"ProjectEditor") -> Self:
        stage = cls(project)
        stage._from_sb3(stage,data)

        stage.tempo = data["tempo"]
        stage.t2t_language = data["textToSpeechLanguage"]
        stage.video_state = data["videoState"]
        stage.video_transparency = data["videoTransparency"]
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
    
    @property
    def project(self) -> "ProjectEditor":
        assert self._project
        return self._project
    
AnySprite = Sprite|Stage