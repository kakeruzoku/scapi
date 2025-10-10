from typing import TYPE_CHECKING, Self, TypedDict, Unpack
from .common import generate_id
from .types import SB3Variable,VarType

if TYPE_CHECKING:
    from .sprite import AnySprite

class VariableIn(TypedDict,total=False):
    id:str|None
    value:VarType
    is_cloud:bool

class Variable:
    def __init__(self,name:str,sprite:"AnySprite",**kwargs:Unpack[VariableIn]):
        self.name:str = name
        self._sprite:"AnySprite" = sprite
        self.id:str|None = kwargs.get("id")
        self.value:VarType = kwargs.get("value",0)

        self.is_cloud:bool = kwargs.get("is_cloud",False)
        self.is_global:bool = sprite.is_stage

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
    
    def genarete_id(self):
        if self.id is None:
            self.id = generate_id() #TODO変数を生成させたことでの処理?
        return self.id
    
    def to_sb3(self) -> tuple[str,SB3Variable]:
        id = self.genarete_id()
        if self.is_cloud:
            return id,[self.name,self.value,True]
        else:
            return id,[self.name,self.value]