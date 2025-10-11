from typing import TYPE_CHECKING, Self, TypedDict, Unpack
from .common import generate_id
from .types import SB3Variable,VarType,SB3List

if TYPE_CHECKING:
    from .sprite import AnySprite

class VariableBase:
    def __init__(self,name:str,sprite:"AnySprite",id:str|None=None):
        self.id = id
        self.name = name
        self._sprite = sprite
    
    @property
    def is_global(self) -> bool:
        return self._sprite.is_stage
    
    def genarete_id(self) -> str:
        if self.id is None:
            self.id = generate_id() #TODO変数を生成させたことでの処理?
        return self.id

class Variable(VariableBase):
    def __init__(
            self,name:str,sprite:"AnySprite",id:str|None=None,
            value:VarType=0,is_cloud:bool=False
        ):
        super().__init__(name,sprite,id)
        self.value:VarType = value
        self.is_cloud:bool = is_cloud

    @classmethod
    def from_sb3(cls,id:str,data:SB3Variable,sprite:"AnySprite") -> Self:
        is_cloud = len(data) == 3
        return cls(
            data[0],
            sprite,
            id=id,
            value=data[1],
            is_cloud=is_cloud
        )
    
    def to_sb3(self) -> tuple[str,SB3Variable]:
        id = self.genarete_id()
        if self.is_cloud:
            return id,[self.name,self.value,True]
        else:
            return id,[self.name,self.value]

class List(VariableBase):
    def __init__(
            self,name:str,sprite:"AnySprite",id:str|None=None,
            value:list[VarType]|None=None
        ):
        super().__init__(name,sprite,id)
        self.value:list[VarType] = value or []

    @classmethod
    def from_sb3(cls,id:str,data:SB3List,sprite:"AnySprite") -> Self:
        return cls(
            data[0],
            sprite,
            id=id,
            value=data[1]
        )
    
    def to_sb3(self) -> tuple[str,SB3List]:
        return self.genarete_id(),[self.name,self.value]

class Broadcast(VariableBase):
    def __init__(self,name:str,sprite:"AnySprite",id:str|None=None,):
        super().__init__(name,sprite,id)

    @classmethod
    def from_sb3(cls,id:str,data:str,sprite:"AnySprite"):
        return cls(data,sprite,id=id)
    
    def to_sb3(self) -> tuple[str, str]:
        return self.genarete_id(),self.name