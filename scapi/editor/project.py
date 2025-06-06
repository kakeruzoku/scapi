from . import info,sprite,monitor,common,base
from ..sites import session
import os
import zipfile
import json
class ScratchProject(base.Base):
    def __init__(self):
        self.info:info.Info = info.Info()
        self._sprites:dict[str,sprite.Sprite] = {}
        self._monitors:dict[str,monitor.MonitorBlock] = {}
        self.protect = True
        self._session:session.Session|None = None
    
    # sprite
    @property
    def sprites(self) -> list[sprite.Sprite]:
        return list(self._sprites.values())
    
    def get_sprite(self,name:str) -> sprite.Sprite | None:
        return self._sprites.get(name)
    
    @property
    def stage(self) -> sprite.Stage:
        return self.get_sprite("Stage") #悩み中
    
    def create_sprite(self,name:str) -> sprite.Sprite:
        _sprite = sprite.Sprite(self,name)
        self._sprites[name] = _sprite
        return _sprite

    # 変換
    def from_sb3(self, project_json:dict) -> None:
        meta = project_json.get("meta", {})
        self.info.useragent = meta.get("agent", "Unknown Agent")
        self.info.semver = meta.get("semver", "0.0.0")
        self.info.vm = meta.get("vm", "0.0.0")

        targets = project_json.get("targets", [])
        self._sprites = {}
        for sprite_data in targets:
            self._sprites[sprite_data["name"]] = sprite.Sprite.from_sb3(sprite_data, self)
        
        monitors = project_json.get("monitors", [])
        self._monitors = {}
        for monitor_data in monitors:
            self._monitors[monitor_data["id"]] = monitor.MonitorBlock.from_sb3(monitor_data, self)

    def to_sb3(self):
        pass

    @classmethod
    def new_project(cls):
        new_project = cls()
        new_project._sprites["Stage"] = sprite.Stage(new_project)

def load_sb3(file_path:str) -> ScratchProject:
    if os.path.isdir(file_path):
        if "project.json" not in os.listdir(file_path):
            raise FileNotFoundError("project.json not found in the directory.")
        
        with open(f"{file_path}/project.json", 'r', encoding='utf-8') as f:
            project_json = json.load(f)
    
    elif file_path.endswith(".sb3") or file_path.endswith(".zip"):
        with zipfile.ZipFile(file_path, 'r') as zf:
            
            if "project.json" not in zf.namelist():
                raise FileNotFoundError("project.json not found in the SB3 file.")
            with zf.open("project.json") as f:
                project_json = json.load(f)
    else:
        raise ValueError("Invalid file type. Please provide a .sb3, .zip file or a directory containing project.json.")
    project = ScratchProject()
    project.from_sb3(project_json)
    return project