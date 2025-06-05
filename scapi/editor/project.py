from . import info,sprite,common,base
from ..sites import session

class ScratchProject(base.Base):
    def __init__(self):
        self.info:info.Info = info.Info()
        self._sprites:dict[str,sprite.Sprite] = {}
        self.protect = True
        self._session:session.Session|None = None
    
    # sprite
    @property
    def sprites(self) -> list[sprite.Sprite]:
        return list(self._sprites.values())
    
    def get_sprite(self,name:str) -> sprite.Sprite | None:
        return self._sprites.get(name)
    
    @property
    def stage(self) -> sprite.Stage:
        return self.get_sprite("Stage") #悩み中
    
    def create_sprite(self,name:str) -> sprite.Sprite:
        _sprite = sprite.Sprite(self,name)
        self._sprites[name] = _sprite
        return _sprite

    # 変換

    def to_sb3(self):
        pass

    @classmethod
    def new_project(cls):
        new_project = cls()
        new_project._sprites["Stage"] = sprite.Stage(new_project)