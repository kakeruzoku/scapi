from typing import TYPE_CHECKING
from . import common,base

if TYPE_CHECKING:
    from . import sprite

class Variable(base.Base):
    def __init__(self,*,_sprite:"sprite.Sprite|sprite.Stage",name:str,value:str|int|float|bool|None=0,id:str):
        self._sprite:"sprite.Sprite|sprite.Stage" = _sprite
        self.name:str = name
        self.value:str|int|float|bool|None = value
        self.id = id or common.create_new_id()

    @property
    def is_global(self) -> bool:
        return self._sprite._is_stage