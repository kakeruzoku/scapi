import io
from enum import Enum
from typing import TypeVar,Any
import struct
import traceback

_T = TypeVar("_T")

# わけわからん

class _Reference:
    def __hash__(self) -> int:
        return hash(id(self))

    def __repr__(self):
        try:
            return f"<参照:{self.number}/{self.obj_list[self.number]}>"
        except Exception:
            return f"<参照:{self.number}>"
        
    def __eq__(self,value):
        try:
            return self.get() == value
        except Exception:
            return None

    def __init__(self,number:int,obj_list:list):
        self.number = number
        self.obj_list = obj_list

    def get(self):
        return self.obj_list[self.number]

class Sound:
    def __repr__(self):
        return f"<Sound {self.length}>"
    
    def __init__(self,length:int,data:bytes):
        self.length = length
        self.data = data

class Bitmap:
    def __repr__(self):
        return f"<Bitmap {self.length}>"
    
    def __init__(self,length:int,data:bytes):
        self.length = length
        self.data = data


class Rectangle: #33
    def __repr__(self):
        return f"<Rectangle x1:{self.x1} y1:{self.y1} x2:{self.x2} y2:{self.y2}>"
    
    def __init__(self,x1,y1,x2,y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

class Point: #33
    def __repr__(self):
        return f"<Rectangle x:{self.x} y:{self.y}>"
    
    def __init__(self,x,y):
        self.x = x
        self.y = y

class Form: #34/35
    def __repr__(self):
        return f"<Form {self.width} {self.height} {self.depth} {self.byte} {self.colormap}>"

    def __init__(self,width:int,height:int,depth:int,byte,colormap=None):
        self.width:int = width
        self.height:int = height
        self.depth:int = depth
        self.byte = byte
        self.colormap = colormap

class Color: #30/31
    def __repr__(self):
        return f"<Color {self.r} {self.g} {self.b} {self.alpha}>"

    def __init__(self,r:int,g:int,b:int,alpha:int|None=None):
        self.r = r
        self.g = g
        self.b = b
        self.alpha = alpha

class Dict:
    def __repr__(self) -> str:
        return f"<Dict {{ {",".join([f"{i[0]}:{i[1]}" for i in (list(self._data.items())+list(self._refdata.items()))])} }}>"
    
    def __init__(self):
        self._data:dict = {}
        self._refdata:dict[_Reference,Any] = {}
    
    def __getitem__(self,key:str):
        try:
            return self._data[key]
        except KeyError:
            pass
        for k,v in list(self._refdata.items()):
            if isinstance(k,_Reference):
                try:
                    value = k.get()
                    self._data[value] = v
                    self._refdata.pop(k)
                    if value == key:
                        return v
                except IndexError:
                    pass
        raise KeyError


    def __setitem__(self,key,value):
        if isinstance(key,_Reference):
            self._refdata[key] = value
        else:
            self._data[key] = value

class _UserClass:
    def __repr__(self):
        return f"<_UserClass {self.type} {self.version} {self.length} {" ".join([str(i) for i in self.fields])}>"

    def __init__(self,type:int,version:int,length:int):
        self.type = type
        self.version = version
        self.length = length
        self.fields = []

    def append(self,obj):
        self.fields.append(obj)

    def read(self,f:io.BytesIO,o:list):
        for _ in range(self.length):
            self.append(_read_obj(f,o))

    def __getitem__(self,key):
        return self.fields[key]

def _load(obj):
    #while True:
    for _ in range(100): #無限ループ対策
        if not isinstance(obj,_Reference):
            return obj
        obj = obj.obj_list[obj.number]
    raise ValueError()

def _read_int(f:io.BytesIO,byte:int=4) -> int:
    return int.from_bytes(f.read(byte))

def _debug_return(f):
    def _func(*l,**d):
        _r = f(*l,**d)
        #print(_r)
        return _r
    return _func

@_debug_return
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
            return struct.unpack('d', f.read(8))[0]
        case 9|10|14: #文字列 (9:ASCII 14:utf-8)
            length = _read_int(f)
            return f.read(length).decode()
        case 11: #bytes
            length = _read_int(f)
            return f.read(length)
        case 12:
            length = _read_int(f) * 2
            return Sound(length,f.read(length))
        case 13:
            length = _read_int(f) * 4
            return Bitmap(length,f.read(length))
        case 20|21|22|23: #list? 違いはわからん
            data = []
            for _ in range(_read_int(f)):
                data.append(_read_obj(f,o))
            return data
        case 24: #dict?
            data = Dict()
            for _ in range(_read_int(f)): #辞書の長さ？
                key = _read_obj(f,o)
                value = _read_obj(f,o)
                data[key] = value
            return data
        case 30|31:
            rgb = _read_int(f)
            r = (rgb >> 22) & 0xff
            g = (rgb >> 12) & 0xff
            b = (rgb >> 2) & 0xff
            alpha = None if types == 30 else _read_int(f,1)
            return Color(r,g,b,alpha)
        case 32:
            return Point(*[_read_obj(f,o) for _ in range(2)])
        case 33:
            return Rectangle(*[_read_obj(f,o) for _ in range(4)])
        case 34|35:
            width = _read_obj(f,o)
            height = _read_obj(f,o)
            depth = _read_obj(f,o)
            _read_obj(f,o) #未使用 常にNone
            byte = _read_obj(f,o)
            colormap = None if types == 34 else _read_obj(f,o)
            return Form(width,height,depth,byte,colormap)
        case 99: #さんしょー
            return _Reference(_read_int(f,3),o)
        case x if 100 <= x:
            version = _read_int(f,1)
            length = _read_int(f,1)
            _uc = _UserClass(x,version,length)
            _uc.read(f,o)
            return _uc
        case x:
            raise TypeError(f"unknown type:{x}")

        

def _read_objectstore(f:io.BytesIO):
    obj_list:list = [None] #番号は1から始まる
    if f.read(10) != b"ObjS\x01Stch\x01":
        raise ValueError()
    obj_count = _read_int(f)
    try:
        for _ in range(obj_count):
            obj_list.append(_read_obj(f,obj_list))
        er = None
    except Exception:
        er = traceback.format_exc()



def load_from_sb(path:str):
    with open(path,"rb") as f:
        if f.read(10) != b"ScratchV02": #ヘッダー
            raise ValueError()
        infosize = int.from_bytes(f.read(4)) #info objのサイズ
        with io.BytesIO(f.read(infosize)) as infoobj:
            _read_objectstore(infoobj)
        with io.BytesIO(f.read()) as mainobj:
            _read_objectstore(mainobj)

