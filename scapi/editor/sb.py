import io
from enum import Enum
from typing import TypeVar
import struct
import traceback

_T = TypeVar("_T")

# わけわからん

class _reference:
    def __repr__(self):
        return f"参照:{self.number}"

    def __init__(self,number:int,obj_list:list):
        self.number = number
        self.obj_list = obj_list

class form: #34/35
    def __repr__(self):
        return f"form {self.width} {self.height} {self.depth}"

    def __init__(self,width:int,height:int,depth:int,byte,colormap=None):
        self.width:int = width
        self.height:int = height
        self.depth:int = depth
        self.byte = byte
        self.colormap = colormap

class color: #30/31
    def __repr__(self):
        return f"color {self.r} {self.g} {self.b} {self.alpha}"

    def __init__(self,r:int,g:int,b:int,alpha:int|None=None):
        self.r = r
        self.g = g
        self.b = b
        self.alpha = alpha

def _load(obj,obj_list:list):
    #while True:
    for _ in range(100): #無限ループ対策
        if not isinstance(obj,_reference):
            return obj
        obj = obj_list[obj.number]
    raise ValueError()

def _read_int(f:io.BytesIO,byte:int=4) -> int:
    return int.from_bytes(f.read(byte))

def _read_obj(f:io.BytesIO,o:list):
    types = _read_int(f,1)
    match types:
        case 1:
            return None
        case 2:
            return True
        case 3:
            return False
        case 4: #4byte整数
            return _read_int(f)
        case 5: #2byte整数
            return _read_int(f,2)
        case 8: #float?
            #return f.read(16)
            return struct.unpack('d', f.read(8))[0]
        case 9|14: #文字列 (9:ASCII 14:utf-8)
            length = _read_int(f)
            return f.read(length).decode()
        case 11: #bytes
            length = _read_int(f)
            return f.read(length)
        case 20: #list?
            data = []
            for _ in range(_read_int(f)):
                data.append(_read_obj(f,o))
            return data
        case 24: #dict?
            data = {}
            for _ in range(_read_int(f)): #辞書の長さ？
                key = _read_obj(f,o)
                value = _read_obj(f,o)
                data[key] = value
            return data
        case 30|31:
            r = _read_int(f,2)
            g = _read_int(f,2)
            b = _read_int(f,2)
            alpha = None if types == 30 else _read_int(f,8)
            return color(r,g,b,alpha)
        case 34|35:
            width = _read_obj(f,o)
            height = _read_obj(f,o)
            depth = _read_obj(f,o)
            _read_obj(f,o) #未使用 常にNone
            byte = _read_obj(f,o)
            colormap = None if types == 34 else _read_obj(f,o)
            return form(width,height,depth,byte,colormap)


        case 99: #さんしょー
            return _reference(_read_int(f,3),o)
        case _:
            raise TypeError(f"unknown type:{types}")

        

def _read_objectstore(f:io.BytesIO):
    obj_list = [None] #番号は1から始まる
    if f.read(10) != b"ObjS\x01Stch\x01":
        raise ValueError()
    obj_count = _read_int(f)
    print(obj_count)
    try:
        for _ in range(obj_count):
            obj_list.append(_read_obj(f,obj_list))
    except Exception:
        traceback.print_exc()
    print("\n".join([str(i) for i in obj_list]))
    print(len(obj_list),obj_count)



def load_from_sb(path:str):
    with open(path,"rb") as f:
        if f.read(10) != b"ScratchV02": #ヘッダー
            raise ValueError()
        infosize = int.from_bytes(f.read(4)) #info objのサイズ
        with io.BytesIO(f.read(infosize)) as infoobj:
            _read_objectstore(infoobj)

