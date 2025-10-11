from typing import Any, Iterable, Self,Unpack,TypedDict
from .types import SB3Project
from ..utils.common import __version__
from .info import Info
from .sprite import Sprite,Stage
from .variable import Variable

class ProjectIn(TypedDict,total=False):
    info:Info
    sprites:list[Sprite]
    stage:Stage
    extensions:list[str]

class ProjectEditor:
    """
    Scratchのプロジェクトデータ。

    Attributes:
        info (Info): プロジェクトのメタデータ。
    """
    def __init__(self,**kwargs:Unpack[ProjectIn]):
        self.info:Info = kwargs.get("info") or Info()
        self.extensions:list[str] = kwargs.get("extensions",[])

        #spriteのロード
        sprites = kwargs.get("sprites")
        self._sprites:dict[str,Sprite] = {}

        stage = kwargs.get("stage")
        if stage is None:
            self._stage = Stage(self)
        else:
            stage._add_to_project(self)
            self._stage = stage

        if sprites is not None:
            for sprite in sprites:
                sprite._add_to_project(self)
                self._sprites[sprite.name] = sprite

    @property
    def sprites(self) -> Iterable[Sprite]:
        """
        スプライトの一覧を返す。

        Returns:
            Iterable[Sprite]:
        """
        return self._sprites.values()
    
    def create_sprite(self,name:str) -> Sprite:
        if name in self._sprites:
            raise ValueError(f"Sprite name:{name} already exists.")
        sprite = Sprite(name,project=self)
        self._sprites[name] = sprite
        return sprite
    
    def use_sprite(self,sprite:Sprite):
        if sprite.name in self._sprites:
            raise ValueError(f"Sprite name:{sprite.name} already exists.")
        sprite._add_to_project(self)
        self._sprites[sprite.name] = sprite
    
    @property
    def stage(self) -> Stage:
        """
        プロジェクトのステージ

        Returns:
            Stage:
        """
        assert self._stage
        return self._stage

    @classmethod
    def from_sb3(cls, data:SB3Project) -> Self:
        stage:Stage|None = None
        sprites:list[Sprite] = []
        for target in data["targets"]:
            if target["isStage"] == True:
                stage = Stage.from_sb3(target)
            else:
                sprites.append(Sprite.from_sb3(target))
        
        if stage is None:
            stage = Stage()

        return cls(
            sprites=sprites,
            stage=stage,
            extensions=data["extensions"]
        )
    
    def to_sb3(self) -> SB3Project:
        return {
            "meta":self.info.to_sb3(),
            "extensions":self.extensions,
            "monitors":[],
            "targets":[self.stage.to_sb3()] + [sprite.to_sb3() for sprite in self.sprites]
        }