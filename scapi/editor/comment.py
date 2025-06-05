from typing import TYPE_CHECKING,Literal
from . import common,base

if TYPE_CHECKING:
    from . import sprite,block

class Comment(base.Base):
    def __init__(self,_sprite:"sprite.Sprite",text:str,_block:"block.Block|None"=None,id:str|None=None):
        self.id = id or common.create_new_id()
        self.text:str = text
        self._sprite = _sprite
        self._block = _block
        self.height:int = 200
        self.width:int = 200
        self.x:int = 0
        self.y:int = 0