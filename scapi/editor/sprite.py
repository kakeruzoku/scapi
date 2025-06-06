from . import block,base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import project

class Sprite(base.Base):
    def __init__(self,*,_project:"project.ScratchProject",name:str):
        self._project:"project.ScratchProject" = _project
        self._name:str = name
        self._is_stage:bool = False
        self._variables:dict = {}
        self._lists:dict = {}

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self,new_name:str):
        self._name = new_name
        self._project._sprites.pop(new_name)
        self._project._sprites[new_name] 

    #var


class Stage(Sprite):
    def __init__(self,*,_project:"project.ScratchProject"):
        super().__init__(_project=_project,name="Stage")
        self._project: "project.ScratchProject" = _project
        self._is_stage:bool = True
        self._variables:dict = {}
        self._lists:dict = {}
        self._broadcasts:dict = {}

    # broadcasts

def load_sprite(sprite_data:dict,*,_project:"project.ScratchProject") -> Stage | Sprite:
    if sprite_data["isStage"]:
        stage = Stage(_project=_project)
        stage._name = sprite_data["name"]
        stage._variables = sprite_data.get("variables", {})
        stage._lists = sprite_data.get("lists", {})
        stage._broadcasts = sprite_data.get("broadcasts", {})
        # ブロックとかx,y,音量とかの追加も必要です……。
        return stage
    else:
        sprite = Sprite(_project=_project,name=sprite_data["name"])
        sprite._name = sprite_data["name"]
        sprite._variables = sprite_data.get("variables", {})
        sprite._lists = sprite_data.get("lists", {})
        return sprite