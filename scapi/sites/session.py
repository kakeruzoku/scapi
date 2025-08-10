import zlib
import base64
import json
from typing import Any
from ..others import common
from . import base

class SessionStatus:
    def __init__(self,session:"Session",data:dict):
        pass

class Session(base._BaseSiteAPI):
    update_type="POST"
    update_url="https://scratch.mit.edu/session/"

    def __init__(self,session_id:str):
        self.session_id:str = session_id
        self.status:SessionStatus|None = None
        
        self.decode_session()

    def decode_session(self):
        s1,s2,s3 = self.session_id.strip('".').split(':')[0]

        padding = '=' * (-len(s1) % 4)
        compressed = base64.urlsafe_b64decode(s1 + padding)
        decompressed = zlib.decompress(compressed)
        data:dict[str,Any] = json.loads(decompressed.decode('utf-8'))
        self._xtoken:str|None = data.get("token")
        self._username:str|None = data.get("username",None)
        self._user_id:int|None = data.get("_auth_user_id",None)
        self.ip:str|None = data.get("login-ip",None)

        self._logged_at:int = common.b62decode(s2)

    @property
    def logged_at(self):
        return common.timestamp_to_dt(self._logged_at)