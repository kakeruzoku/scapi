import io
from enum import Enum

class _object_type(Enum):
    Dict=24

# わけわからん

def _read_objectstore(f:io.BytesIO):
    obj_list = []
    if f.read(10) != b"ObjS\x01Stch\x01":
        raise ValueError()
    obj_count = int.from_bytes(f.read(4))
    for _ in range(obj_count):
        types = int.from_bytes(f.read(1))

def load_from_sb(path:str):
    with open(path,"rb") as f:
        if f.read(10) != b"ScratchV02":
            raise ValueError()
        infosize = int.from_bytes(f.read(4))
        with io.BytesIO(f.read(infosize)) as infoobj:
            _read_objectstore(infoobj)