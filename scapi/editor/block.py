from enum import Enum
import dataclasses
from typing import Callable,TypeVar,TYPE_CHECKING

_T = TypeVar("_T")

@dataclasses.dataclass(frozen=True)
class BlockType:
    name:str
    is_block:bool
    #IF is_block:
    is_top:bool = False
    is_bottom:bool = False
    is_c:bool = False
    #ELSE:
    is_reporter:bool = False
    is_boolean:bool = False
    is_menu:bool = False

    def __str__(self):
        return self.name
    
    def __call__(self, block):
        return self


class BlockTypes:
    hat = BlockType("Hat",True,is_top=True)
    stack = BlockType("Stack",True)
    cap = BlockType("Cap",True,is_bottom=True)
    c = BlockType("C",True,is_c=True)
    c_cap = BlockType("C_cap",True,is_c=True,is_bottom=True)
    reporter = BlockType("Reporter",False,is_reporter=True)
    boolean = BlockType("Boolean",False,is_reporter=True,is_boolean=True)
    menu = BlockType("Menu",False,is_menu=True)



@dataclasses.dataclass(frozen=True)
class BlockCategory:
    name:str
    color:int #0x
    extension:str|None=None

    @property
    def is_extension(self) -> bool:
        return self.extension is not None
    
    
class BlockCategories:
    motion=BlockCategory("Motion",0x4c97ff)
    looks=BlockCategory("Looks",0x9966ff)
    sound=BlockCategory("Sound",0xd65cd6)
    events=BlockCategory("Events",0xffd500)
    control=BlockCategory("Control",0xffab19)
    sensing=BlockCategory("Sensing",0x4cbfef)
    operators=BlockCategory("Operators",0x40bf4a)
    variables=BlockCategory("Variables",0xff8c1a)
    list=BlockCategory("List",0xff661a)
    my_blocks=BlockCategory("My Blocks",0xff666c)

    translate=BlockCategory("Translate",0x0fbd8c,"translate")
    music=BlockCategory("Music",0x0fbd8c,"music")
    pen=BlockCategory("Pen",0x0fbd8c,"pen")
    video_sensing=BlockCategory("Video Sensing",0x0fbd8c,"videoSensing")
    text_to_speech=BlockCategory("Text to Speech",0x0fbd8c,"text2speech")
    makey_makey=BlockCategory("Makey Makey",0x0fbd8c,"makeymakey")
    micro_bit=BlockCategory("micro:bit",0x0fbd8c,"microbit")
    lego_ev3=BlockCategory("LEGO EV3",0x0fbd8c,"ev3")
    boost=BlockCategory("BOOST",0x0fbd8c,"boost")
    wedo2_0=BlockCategory("WeDo 2.0",0x0fbd8c,"wedo2")
    force_and_acceleration=BlockCategory("Force_and_Acceleration",0x0fbd8c,"gdxfor")


@dataclasses.dataclass(frozen=True)
class BlockInfo:
    name:str
    category:BlockCategory
    opcode_sb3:str
    opcode_sb2:str|None=None
    _type:"Callable[[Block],BlockType]" = BlockTypes.stack
    # 全てを止めるブロックが変わることがあるので関数で実装
    # ふつうに BlockTypes.stack とかでもOK
    sprites_only:bool=False

class BlockList:
    movesteps=BlockInfo("movesteps",BlockCategories.motion,"motion_movesteps","forward:",BlockTypes.stack,True)
    turnright=BlockInfo("turnright",BlockCategories.motion,"motion_turnright","turnRight:",BlockTypes.stack,True)
    turnleft=BlockInfo("turnleft",BlockCategories.motion,"motion_turnleft","turnLeft:",BlockTypes.stack,True)


# BlockInfo("",BlockCategories,"","")

class BlockGroup: pass

class Block: pass