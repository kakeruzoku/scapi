from typing import Any, LiteralString
from .common import Base
from ..utils.common import __version__
from .types import SB3Meta

class Info(Base):
    
    @property
    def user_agent(self) -> LiteralString:
        return f"Scapi Scratch editor {__version__}"
    
    @property
    def vm(self) -> LiteralString:
        return __version__
    
    def to_sb3(self) -> SB3Meta:
        return {
            "agent":self.user_agent,
            "semver":"3.0.0",
            "vm":self.vm
        }