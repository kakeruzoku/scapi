from typing import Any, Iterable, Self,Unpack,TypedDict
from .types import SB3Project
from ..utils.common import __version__
from .info import Info
from .sprite import Sprite,Stage

class ProjectIn(TypedDict,total=False):
    info:Info
    sprites:list[Sprite]
    stage:Stage
    extensions:list[str]

class Project:
    """
    Scratchのプロジェクトデータ。

    Attributes:
        info (Info): プロジェクトのメタデータ。
    """
    def __init__(self,**kwargs:Unpack[ProjectIn]):
        self.info:Info = kwargs.get("info") or Info()

        #spriteのロード
        sprites = kwargs.get("sprites")
        self._sprites:dict[str,Sprite] = {}
        if sprites is not None:
            for sprite in sprites:
                sprite._add_to_project(self)
                self._sprites[sprite.name] = sprite
        
        stage = kwargs.get("stage")
        self._stage:Stage|None = None
        self.stage = stage or Stage(self)

        self.extensions:list[str] = kwargs.get("extensions",[])

    @property
    def sprites(self) -> Iterable[Sprite]:
        """
        スプライトの一覧を返す。

        Returns:
            Iterable[Sprite]:
        """
        return self._sprites.values()
    
    @property
    def stage(self) -> Stage:
        """
        プロジェクトのステージ

        Returns:
            Stage:
        """
        assert self._stage
        return self._stage
    
    @stage.setter
    def stage(self,value:Stage):
        value._add_to_project(self)
        self._stage = value

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
            "targets":[]
        }