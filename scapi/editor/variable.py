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


class VariableIn(TypedDict,total=False):
    id:str|None
    value:VarType
    is_cloud:bool

class Variable(VariableBase):
    def __init__(self,name:str,sprite:"AnySprite",**kwargs:Unpack[VariableIn]):
        super().__init__(name,sprite,kwargs.get("id"))
        self.value:VarType = kwargs.get("value",0)

        self.is_cloud:bool = kwargs.get("is_cloud",False)

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


class ListIn(TypedDict,total=False):
    id:str|None
    value:list[VarType]

class List(VariableBase):
    def __init__(self,name:str,sprite:"AnySprite",**kwargs:Unpack[ListIn]):
        super().__init__(name,sprite,kwargs.get("id"))
        self.value:list[VarType] = kwargs.get("value",[])

    @classmethod
    def from_sb3(cls,id:str,data:SB3List,sprite:"AnySprite") -> Self:
        return cls(
            data[0],
            sprite,
            id=id,
            value=data[1]
        )
    
    def to_sb3(self) -> tuple[str,SB3List]:
        id = self.genarete_id()
        return id,[self.name,self.value]