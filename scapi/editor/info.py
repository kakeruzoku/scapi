from typing import Any, LiteralString
from ..utils.common import __version__
from .types import SB3Meta

class Info:
    """
    プロジェクトのメタデータ。
    """
    
    @property
    def user_agent(self) -> LiteralString:
        """
        プロジェクト用のUserAgentを返す

        Returns:
            str: 
        """
        return f"Scapi Scratch editor {__version__}"
    
    @property
    def vm(self) -> LiteralString:
        """
        Scapiのバージョンを返す

        Returns:
            str: 
        """
        return __version__
    
    def to_sb3(self) -> SB3Meta:
        return {
            "agent":self.user_agent,
            "semver":"3.0.0",
            "vm":self.vm
        }