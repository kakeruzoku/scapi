from typing import Any,Self


class Base:
    @classmethod
    def from_sb3(cls,data) -> Self:
        raise TypeError()
    
    @classmethod
    def from_sb2(cls,data) -> Self:
        raise TypeError()
    
    def to_sb3(self) -> Any:
        raise TypeError()
    
    def to_sb2(self) -> Any:
        raise TypeError()