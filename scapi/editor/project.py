from typing import Any, Iterable, Self,Unpack,TypedDict
from .types import SB3Project,SB3Sprite
from ..utils.common import __version__
from .info import Info
from .sprite import Sprite,Stage
from .variable import Variable

class ProjectEditor:
    """
    Scratchのプロジェクトデータ。

    Attributes:
        info (Info): プロジェクトのメタデータ。
    """
    info:Info
    extensions:list[str]
    _stage:Stage

    def __init__(self):
        self._sprites:dict[str,Sprite] = {}
        self._sprite_layer:list[Sprite] = [] #<-後ろ 前->

    def _init(self):
        self.info = Info()
        self.extensions = []
        self._stage = Stage(self)

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
    
    @classmethod
    def new(cls) -> Self:
        project = cls()
        project._init()
        return project

    @classmethod
    def from_sb3(cls, data:SB3Project) -> Self:
        project = cls()
        project.info = Info()
        project.extensions = data["extensions"]

        sprites:list[SB3Sprite] = []
        for target in data["targets"]:
            if target["isStage"] == True:
                project._stage = Stage.from_sb3(target,project)
            else:
                sprites.append(target)

        project._sprites = {i.name:i for i in [Sprite.from_sb3(i,project) for i in sprites]}
        project._sprite_layer = sorted(project._sprites.values(),key=lambda sprite: sprite.layer_order or 0)
        return project
    
    def to_sb3(self) -> SB3Project:
        return {
            "meta":self.info.to_sb3(),
            "extensions":self.extensions,
            "monitors":[],
            "targets":[self.stage.to_sb3()] + [sprite.to_sb3() for sprite in self.sprites]
        }