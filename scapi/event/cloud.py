from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Iterable
import aiohttp
import json
from .base import _BaseEvent
from ..utils.client import HTTPClient
from ..sites.activity import CloudActivity
from ..utils.types import (
    WSCloudActivityPayload
)

if TYPE_CHECKING:
    from ..sites.session import Session

class _BaseCloud(_BaseEvent):
    max_length:int|None = None

    def __init__(
            self,
            url:str,
            project_id:int|str,
            username:str,
            client:HTTPClient,
            timeout:aiohttp.ClientWSTimeout|None=None
        ):
        super().__init__()
        self.url = url

        self.client:HTTPClient = client or HTTPClient()
        self.session:"Session|None" = None
        self._ws:aiohttp.ClientWebSocketResponse|None = None
        self.header:dict[str,str] = {}
        self.project_id = project_id
        self.username = username

        self._data:dict[str,str] = {}

        self.timeout = timeout or aiohttp.ClientWSTimeout(ws_receive=None, ws_close=10.0) # pyright: ignore[reportCallIssue]

    @property
    def ws(self) -> aiohttp.ClientWebSocketResponse:
        if self._ws is None:
            raise ValueError("Websocket is None")
        return self._ws
    
    async def _send(self,data:Iterable):
        text = "".join([json.dumps(i)+"\n" for i in data])
        await self.ws.send_str(text)


    async def _handshake(self):
        await self._send([{
            "method":"handshake",
            "user":self.username,
            "project_id":str(self.project_id)
        }])

    def _received_data(self,datas):
        if isinstance(datas,bytes):
            try:
                datas = datas.decode()
            except ValueError:
                return
        for raw_data in datas.split("\n"):
            try:
                data:WSCloudActivityPayload = json.loads(raw_data,parse_constant=str,parse_float=str,parse_int=str)
            except json.JSONDecodeError:
                continue
            if not isinstance(data,dict):
                continue
            method = data.get("method","")
            if method != "set":
                continue
            self._call_event(self.on_set,CloudActivity._create_from_ws(data,self))

    async def _event_monitoring(self,event:asyncio.Event):
        wait_count = 0
        while True:
            try:
                async with self.client._session.ws_connect(
                    self.url,
                    headers=self.header,
                    timeout=self.timeout
                ) as ws:
                    self._ws = ws
                    await self._handshake()
                    self._call_event(self.on_connect)
                    wait_count = 0
                    async for w in ws:
                        if w.type in (
                            aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.CLOSING,
                            aiohttp.WSMsgType.CLOSE,
                            aiohttp.WSMsgType.ERROR
                        ):
                            raise Exception
                        if self.is_running:
                            self._received_data(w.data)
            except Exception:
                self._call_event(self.on_disconnect,wait_count)
                await asyncio.sleep(wait_count)
                wait_count += 2
            await event.wait()

    async def on_connect(self):
        pass

    async def on_set(self,activity:CloudActivity):
        pass

    async def on_disconnect(self,interval:int):
        pass