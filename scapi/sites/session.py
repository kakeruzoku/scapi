import zlib
import base64
import json
from typing import Any
from ..others import client, common
from . import base
from ..others.types import (
    DecodedSessionID
)

def decode_session(session_id:str) -> tuple[DecodedSessionID,int]:
    s1,s2,s3 = session_id.strip('".').split(':')

    padding = '=' * (-len(s1) % 4)
    compressed = base64.urlsafe_b64decode(s1 + padding)
    decompressed = zlib.decompress(compressed)
    return json.loads(decompressed.decode('utf-8')),common.b62decode(s2)

class SessionStatus:
    def __init__(self,session:"Session",data:dict):
        pass

class Session(base._BaseSiteAPI):
    update_type="POST"
    update_url="https://scratch.mit.edu/session/"

    def __init__(self,session_id:str,*,_client:client.HTTPClient|None=None):
        self.client = _client or client.HTTPClient()
        
        super().__init__(self)
        self.session_id:str = session_id
        self.status:SessionStatus|None = None
        
        decoded,login_dt = decode_session(self.session_id)

        self.xtoken = decoded.get("token")
        self.username = decoded.get("username")
        self.login_ip = decoded.get("login-ip")
        self.user_id = common.try_int(decoded.get("_auth_user_id"))
        self._logged_at = login_dt

    @property
    def logged_at(self):
        return common.timestamp_to_dt(self._logged_at)