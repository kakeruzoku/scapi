from . import block,base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import project

class Sprite(base.Base):
    def __init__(self,_project:"project.ScratchProject",name:str):
        self._project:"project.ScratchProject" = _project
        self._blocks:list[block.Block] = []
        self._name:str = name
        self._variable:dict = {}

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
    def __init__(self,project:"project.ScratchProject"):
        super().__init__(project,"Stage")

    # broadcasts