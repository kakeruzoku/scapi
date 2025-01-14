import asyncio
import json
import time
from typing import TYPE_CHECKING
import warnings
import aiohttp
from ..others import common
import async_timeout
import re

if TYPE_CHECKING:
    from ..sites.session import Session
    from ..sites.user import User
    from ..sites.studio import Studio
    from ..sites.project import Project

class _BaseCloud:

    def __init__(self,clientsession:common.ClientSession|None,project_id:int|str):

        self.url:str = ""
        self.origin:str|None = None
        self.cookie:str = ""
        self.header:dict = {}
        self.username:str = "scapi"
        self.project_id:int = common.try_int(project_id)
        self._last_set_time:float = time.time()
        self.max_length:int = 256
        self._ratelimit:float = 0.1

        self._data:dict[str,float|int] = {}

        self._is_close_cs = not isinstance(clientsession,common.ClientSession)
        clientsession = common.create_ClientSession(clientsession)
        self.clientsession:common.ClientSession = clientsession
        self._websocket:aiohttp.ClientWebSocketResponse|None = None
        self._is_connect:bool = False

    @property
    def websocket(self) -> aiohttp.ClientWebSocketResponse|None:
        return self._websocket

    @property
    def is_connect(self) -> bool:
        return isinstance(self.websocket,aiohttp.ClientWebSocketResponse) and (not self.websocket.closed)

    async def _handshake(self,ws:aiohttp.ClientWebSocketResponse):
        await ws.send_json({
            "method":"handshake",
            "user":self.username,
            "project_id":str(self.project_id)
        })

    async def _run(self,timeout=10):
        async with self.clientsession.ws_connect(
            self.url,
            origin=self.origin,
            headers=self.header,
            timeout=timeout
        ) as ws:
            await self._handshake(ws)
            self._websocket = ws
            async for w in self.websocket:
                if not isinstance(w.data,str):
                    continue
                for i in w.data.split("\n"):
                    try:
                        data = json.loads(i)
                    except Exception:
                        continue
                    if not isinstance(data,dict):
                        continue
                    if data.get("method","") != "set":
                        continue
                    self._data[data["name"][2:]] = data["value"]
                    asyncio.create_task(self._on_set(data["name"][2:],data["value"]))

        await self.websocket.close()

    async def _on_set(self,variable:str,value:float|int):
        pass

    async def connect(self,timeout:int=10):
        if self.is_connect:
            raise Exception
        else:
            self._is_connect = True
            asyncio.create_task(self._run(timeout))
            async with async_timeout.timeout(timeout):
                while not self.is_connect:
                    await asyncio.sleep(0.01)
        

    async def close(self):
        await self.websocket.close()
        if self._is_close_cs:
            await self.clientsession.close()

    def get_vars(self) -> dict:
        return self._data.copy()

    def _check_var(self,value):
        value = str(value)
        if len(value) > self.max_length:
            return False
        return re.fullmatch("\-?[1234567890]+(\.[1234567890]+)?",value) is not None
    
    async def _wait(self,n:int=1):
        if self._ratelimit == 0:
            return
        need_waiting_time = (self._last_set_time + (self._ratelimit * n)) - time.time()
        if need_waiting_time <= 0:
            return
        self._last_set_time = self._last_set_time + (self._ratelimit * n)
        await asyncio.sleep(need_waiting_time)

    async def set_var(self,variable:str,value:str|float|int):
        if not self.is_connect: raise
        if not variable.startswith("☁ "):
            variable = "☁ " + variable
        if not self._check_var(value):
            raise ValueError
        await self._wait()

        packet = {
            "method": "set",
            "name": variable,
            "value": str(value),
            "user": self.username,
            "project_id": str(self.project_id),
        }
        await self.websocket.send_str(json.dumps(packet,ensure_ascii=False))
        now = time.time()
        if self._last_set_time < now:
            self._last_set_time = now

    async def set_vars(self,data:dict[str,str|float|int]):
        if not self.is_connect: raise
        packets:str = ""
        c = 0
        for k,v in data.items():
            if not k.startswith("☁ "):
                k = "☁ " + k
            if not self._check_var(v):
                warnings.warn(f"{v} won't set ({k})")
                continue
            packet = {
                "method": "set",
                "name": k,
                "value": str(v),
                "user": self.username,
                "project_id": str(self.project_id),
            }
            c = c + 1
            packets = packets + json.dumps(packet) + "\n"
        
        if c == 0:
            return
        
        await self._wait(c)
        await self.websocket.send_str(packets)
        now = time.time()
        if self._last_set_time < now:
            self._last_set_time = now

    async def __aenter__(self) -> "_BaseCloud":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

class TurboWarpCloud(_BaseCloud):
    
    def __init__(
            self,
            project_id:int|str,
            clientsession:common.ClientSession|None,
            *,
            purpose:str="",
            contact:str="",
            server_url:str="wss://clouddata.turbowarp.org"
        ):
        
        super().__init__(clientsession,project_id)
        self.url = server_url
        self.header["User-Agent"] = f"Scapi(0f.f5.si/scapi)/{common.__version__} (Purpose:{purpose}; Contact:{contact})"
        self.max_length = 100000
        self._ratelimit = 0.0

def get_tw_cloud(
            project_id:int|str,
            clientsession:common.ClientSession|None=None,
            *,
            purpose:str="unknown",
            contact:str="unknown",
            server_url:str="wss://clouddata.turbowarp.org"
        ) -> TurboWarpCloud:
    return TurboWarpCloud(project_id,clientsession,purpose=purpose,contact=contact,server_url=server_url)