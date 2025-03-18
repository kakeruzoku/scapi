import asyncio
import json
import time
from typing import TYPE_CHECKING
import warnings
import aiohttp
from ..others import common,error as exception
import re

if TYPE_CHECKING:
    from ..sites.session import Session
    from ..sites.user import User
    from ..sites.studio import Studio
    from ..sites.project import Project
    from . import cloud_event

class _BaseCloud:

    def __str__(self) -> str:
        return f"<_BaseCloud id:{self.project_id} connect:{self.is_connect}>"

    def __init__(self,clientsession:common.ClientSession|None,project_id:int|str):

        self.url:str = ""
        self._header:dict = {}
        self.username:str = "scapi"
        self.project_id:int = common.try_int(project_id)
        self._last_set_time:float = time.time()
        self.max_length:int = 256
        self._ratelimit:float = 0.1

        self._data:dict[str,str] = {}

        self._is_close_cs = not isinstance(clientsession,common.ClientSession)
        clientsession = common.create_ClientSession(clientsession)
        self.clientsession:common.ClientSession = clientsession
        self._websocket:aiohttp.ClientWebSocketResponse|None = None

        self._event:"cloud_event.CloudEvent|None" = None
        self.tasks:asyncio.Task|None = None

        self._instruction:bool = False
        self._timeout:int = 10

    @property
    def websocket(self) -> aiohttp.ClientWebSocketResponse|None:
        return self._websocket

    @property
    def is_connect(self) -> bool:
        return isinstance(self.websocket,aiohttp.ClientWebSocketResponse) and (not self.websocket.closed)
    
    @property
    def header(self) -> dict:
        return self._header

    async def _handshake(self,ws:aiohttp.ClientWebSocketResponse):
        await ws.send_json({
            "method":"handshake",
            "user":self.username,
            "project_id":str(self.project_id)
        })

    async def _run(self,timeout=10):
        c = 1
        self._timeout = timeout
        self.timeout = aiohttp.ClientWSTimeout(ws_receive=None, ws_close=None)
        while True:
            async with self.clientsession.ws_connect(
                self.url,
                headers=self.header,
                timeout=self.timeout
            ) as ws:
                await self._handshake(ws)
                asyncio.create_task(self._on_connect(self))
                c = 1
                self._websocket = ws
                async for w in self._websocket:
                    if not isinstance(w.data,str):
                        continue
                    for i in w.data.split("\n"):
                        try:
                            data = json.loads(i,parse_constant=str,parse_float=str,parse_int=str)
                        except Exception:
                            continue
                        if not isinstance(data,dict):
                            continue
                        asyncio.create_task(self._on_event(self,data.get("method",""),data["name"][2:],data.get("value",None),data))
                        if data.get("method","") != "set":
                            continue
                        self._data[data["name"][2:]] = data["value"]
            if self._instruction:
                asyncio.create_task(self._on_disconnect(self,c))
                await asyncio.sleep(c)
                if c == 1: c = 3
                c = c + 2
            else:
                break

        await self._websocket.close()

    async def _on_event(self,_self:"_BaseCloud",method:str,variable:str,value:str,other):
        pass

    async def _on_connect(self,_self:"_BaseCloud"):
        print(f"Cloud Connected:{self.url}")

    async def _on_disconnect(self,_self:"_BaseCloud",interval:int):
        print(f"Cloud Disconnected:{self.url} Reconnect after {interval} seconds.")

    async def connect(self,timeout:int=10) -> asyncio.Task:
        self._instruction = True
        if not self.is_connect:
            tasks = asyncio.create_task(self._run(timeout))
            self.tasks = tasks
            try:
                await self._wait_connect(timeout)
            except TimeoutError:
                self.tasks.cancel()
                await self.websocket.close()
                raise
        return self.tasks
        

    async def close(self,is_clientsession_close:bool|None=None):
        self._instruction = False
        if self.is_connect:
            await self.websocket.close()
        if is_clientsession_close is None:
            if self._is_close_cs:
                await self.clientsession.close()
        elif is_clientsession_close:
            await self.clientsession.close()

    def get_vars(self) -> dict[str,str]:
        return self._data.copy()
    
    def get_var(self,variable:str) -> str|None:
        return self._data.get(variable)

    def _check_var(self,value):
        value = str(value)
        if len(value) > self.max_length:
            return False
        return re.fullmatch(r"\-?[1234567890]+(\.[1234567890]+)?",value) is not None
    
    async def _wait(self,n:int=1):
        if self._ratelimit == 0:
            return
        need_waiting_time = (self._last_set_time + (self._ratelimit * n)) - time.time()
        if need_waiting_time <= 0:
            return
        self._last_set_time = self._last_set_time + (self._ratelimit * n)
        await asyncio.sleep(need_waiting_time)

    async def _wait_connect(self,_wait:int):
        if not self._instruction:
            raise exception.CloudConnectionFailed()
        async with asyncio.timeout(_wait):
            while not self.is_connect:
                await asyncio.sleep(0)

    async def set_var(self,variable:str,value:str,_wait:int=20):
        value = str(value)
        await self._wait_connect(_wait)
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

    async def set_vars(self,data:dict[str,str|float|int],_wait:int=20):
        await self._wait_connect(_wait)
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

    def event(self) -> "cloud_event.CloudEvent":
        from . import cloud_event
        return cloud_event.CloudEvent(self)

class TurboWarpCloud(_BaseCloud):
    
    def __str__(self) -> str:
        return f"<TurboWarpCloud id:{self.project_id} connect:{self.is_connect}>"

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