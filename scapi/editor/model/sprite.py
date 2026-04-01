

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from .project import EditorProject


@dataclass(slots=True, kw_only=True)
class SpriteBase:
    is_stage: ClassVar[bool]
    _project: "EditorProject"

    @property
    def project(self) -> "EditorProject":
        return self._project


@dataclass(slots=True, kw_only=True)
class Sprite(SpriteBase):
    is_stage = False
    _name: str

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self.rename(name)

    def rename(self, name: str):
        self._project._assert_duplicate_sprite_name(name)
        self._name = name


@dataclass(slots=True, kw_only=True)
class Stage(SpriteBase):
    is_stage = True
