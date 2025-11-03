from typing import TYPE_CHECKING, Any, Final, Literal, Self, Unpack, TypedDict
from .types import SB3Asset,SB3Costume,SB3Sound

if TYPE_CHECKING:
    from .project import ProjectEditor
    from .sprite import AnySprite

class AssetBase:
    asset_id:str
    name:str

    def __init__(self,sprite:"AnySprite"):
        self._sprite = sprite

class Costume(AssetBase):
    bitmapResolution:int
    ext:Literal["png", "jpg", "jpeg", "svg"]
    rotation_center_x:float
    rotation_center_y:float

    @classmethod
    def from_sb3(cls,data:SB3Costume,sprite:"AnySprite") -> Self:
        costume = cls(sprite)
        costume.asset_id = data.get("assetId")
        costume.name = data.get("name")

        costume.bitmapResolution = data.get("bitmapResolution",1)
        costume.ext = data.get("dataFormat")
        costume.rotation_center_x = data.get("rotationCenterX")
        costume.rotation_center_y = data.get("rotationCenterY")
        return costume

    def to_sb3(self) -> SB3Costume:
        return {
            "assetId":self.asset_id,
            "bitmapResolution":self.bitmapResolution,
            "dataFormat":self.ext,
            "md5ext":f"{self.asset_id}.{self.ext}",
            "name":self.name,
            "rotationCenterX":self.rotation_center_x,
            "rotationCenterY":self.rotation_center_y
        }

class Sound(AssetBase):
    ext:Literal["wav", "mp3"]
    format:str
    rate:int
    sample_count:int

    @classmethod
    def from_sb3(cls,data:SB3Sound,sprite:"AnySprite"):
        costume = cls(sprite)
        costume.asset_id = data.get("assetId")
        costume.name = data.get("name")

        costume.format = data.get("format",1)
        costume.ext = data.get("dataFormat")
        costume.rate = data.get("rate")
        costume.sample_count = data.get("sampleCount")
        return costume

    def to_sb3(self) -> SB3Sound:
        return {
            "assetId":self.asset_id,
            "dataFormat":self.ext,
            "format":self.format,
            "md5ext":f"{self.asset_id}.{self.ext}",
            "name":self.name,
            "rate":self.rate,
            "sampleCount":self.sample_count
        }