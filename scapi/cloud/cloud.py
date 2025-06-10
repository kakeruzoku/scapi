import asyncio
import json
import time
from typing import TYPE_CHECKING, Any, AsyncGenerator
import warnings
import aiohttp
from ..others import common,error as exception
from ..sites import activity,base
import re

if TYPE_CHECKING:
    from . import cloud_event
    from ..sites import project,session

class _BaseCloud:

    def __repr__(self) -> str:
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
        self.clientsession:common.ClientSession = common.create_ClientSession(clientsession)
        self._websocket:aiohttp.ClientWebSocketResponse|None = None

        self._event:"cloud_event.CloudWebsocketEvent|cloud_event.CloudLogEvent|None" = None
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
        await ws.send_str(json.dumps({
            "method":"handshake",
            "user":self.username,
            "project_id":str(self.project_id)
        })+"\n")

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
                is_sync = True
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
                        method = data.get("method","")
                        if method == "set":
                            self._data[data["name"][2:]] = data["value"]
                            if not is_sync:
                                asyncio.create_task(self._on_event(
                                    self,"set",data["name"][2:],data.get("value",None),data
                                ))
                    is_sync = False
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
                await asyncio.sleep(0.1)

    async def _send(self,*packets:dict,_wait:int|None,project_id:int|None=None):
        if len(packets) == 0: return
        _packet = ""
        for p in packets:
            data = {"user":self.username,"project_id":str(project_id or self.project_id)}|p
            _packet = _packet + json.dumps(data,ensure_ascii=False) + "\n"

        await self._wait_connect(_wait or self._timeout)
        await self._wait(len(packets))
        await self._websocket.send_str(_packet)
        now = time.time()
        if self._last_set_time < now:
            self._last_set_time = now

    async def set_var(self,variable:str,value:str,project_id:int|None=None,*,_wait:int|None=None):
        value = str(value)
        if not variable.startswith("☁ "):
            variable = "☁ " + variable
        await self._send(
            {"method": "set","name": variable,"value": str(value)},
            _wait=_wait, project_id=project_id
        )
        self._data[variable[2:]] = value

    async def set_vars(self,data:dict[str,str|float|int],*,project_id:int|None=None,_wait:int|None=None):
        await self._wait_connect(_wait or self._timeout)
        packets:list[dict] = []
        for k,v in data.items():
            if not k.startswith("☁ "):
                k = "☁ " + k
            packets.append({"method": "set","name": k,"value": str(v)})
        await self._send(*packets,_wait=_wait, project_id=project_id)
        for i in packets:
            self._data[i["name"][2:]] = i["value"]

    async def create_var(self,variable:str,value:str="0",*,project_id:int|None=None,_wait:int|None=None):
        value = str(value)
        if not variable.startswith("☁ "):
            variable = "☁ " + variable
        if not self._check_var(value):
            raise ValueError
        
        await self._send(
            {"method": "create","name": variable,"value": value},
            _wait=_wait, project_id=project_id
        )
        self._data[variable[2:]] = value

    async def rename_var(self,old:str,new:str,*,project_id:int|None=None,_wait:int|None=None):
        if not old.startswith("☁ "): old = "☁ " + old
        if not new.startswith("☁ "): new = "☁ " + new

        await self._send(
            {"method": "rename","name": old,"new_name": new},
            _wait=_wait, project_id=project_id
        )
        old_data = self._data.get(old[2:])
        if old_data is not None:
            self._data[new[2:]] = old_data

    async def delete_var(self,variable:str,*,project_id:int|None=None,_wait:int|None=None):
        if not variable.startswith("☁ "):
            variable = "☁ " + variable
        await self._send(
            {"method": "delete","name": variable},
            _wait=_wait, project_id=project_id
        )
        self._data.pop(variable,None)

    async def __aenter__(self) -> "_BaseCloud":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    def event(self) -> "cloud_event.CloudWebsocketEvent":
        from . import cloud_event
        return cloud_event.CloudWebsocketEvent(self)

class ScratchCloud(_BaseCloud):
    def __repr__(self) -> str:
        return f"<ScratchCloud id:{self.project_id} user:{self.username} connect:{self.is_connect}>"

    def __init__(
            self,
            project_id:int|str,
            session:"session.Session"
        ):

        super().__init__(session.ClientSession,project_id)
        self.url = "wss://clouddata.scratch.mit.edu"
        self.Session = session
        self._header = {}
        self._header["Cookie"] = "scratchsessionsid=\"" + self.Session.session_id + "\";"
        self._header["Origin"] = "https://scratch.mit.edu"
        self.username = self.Session.username

    def get_logs(self,limit:int=100,offset:int=0) -> AsyncGenerator[activity.CloudActivity, None]:
        return base.get_object_iterator(
            self.clientsession,f"https://clouddata.scratch.mit.edu/logs",
            None,activity.CloudActivity,self.Session,
            limit=limit,offset=offset,max_limit=100,add_params={"projectid":self.project_id},
            custom_func=base._cloud_activity_iterator_func,others={"project_id":self.project_id}
        )
    
    def log_event(self,interval:float=1) -> "cloud_event.CloudLogEvent":
        from . import cloud_event
        obj = cloud_event.CloudLogEvent(self.project_id,self.clientsession,interval)
        obj.Session = self.Session
        return obj
    
    async def is_log_active(self) -> bool:
        try:
            [i async for i in self.get_logs(limit=1)]
            return True
        except Exception:
           return False

    async def auto_event(self, log_interval: float = 1) -> "cloud_event.CloudWebsocketEvent | cloud_event.CloudLogEvent":
        if await self.is_log_active():
            return self.log_event(log_interval)
        else:
            return self.event()

class TurboWarpCloud(_BaseCloud):
    
    def __repr__(self) -> str:
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