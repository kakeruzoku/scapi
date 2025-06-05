from typing import TYPE_CHECKING,Literal
from . import common,base

if TYPE_CHECKING:
    from . import sprite


class Asset(base.Base):
    def __init__(self,_sprite:"sprite.Sprite",name:str,md5:str,file_ext:str):
        self.name:str = name
        self._sprite = _sprite
        self._md5 = md5
        self.file_ext = file_ext

    @property
    def md5(self):
        return self._md5
    
    @property
    def url(self):
        return f"https://assets.scratch.mit.edu/internalapi/asset/{self._md5}.{self.file_ext}/get/"
    

class Costume(Asset):
    def __init__(
            self,_sprite:"sprite.Sprite",name:str,md5:str,file_ext:Literal["svg","png"],
            rotation_center_x:int|float=0,
            rotation_center_y:int|float=0,
            bitmap_resolution:int|float|None=0
        ):
        super().__init__(_sprite,name,md5,file_ext)
        self.rotation_center_x = rotation_center_x
        self.rotation_center_y = rotation_center_y
        self.bitmap_resolution = bitmap_resolution

class Sound(Asset):
    def __init__(
            self,_sprite:"sprite.Sprite",name:str,md5:str,
            rate:int|None=None,
            sample_count:int|None=None
        ):
        super().__init__(_sprite,name,md5,"wav")
        #Scratch上では無視される
        self.rate = rate
        self.sample_count = sample_count
