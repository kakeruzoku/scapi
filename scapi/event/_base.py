import asyncio
from typing import Any, Awaitable, Callable
from ..others import common

"""
event = _BaseEvent()

@event.event
def on_ready(self):
    print("ready")

@event.event
def test(self):
    print("ping")

event.run(False)
"""

class _BaseEvent:
    def __init__(self,interval:float): #option edit
        self.interval = float(interval)
        self.task:asyncio.Task|None = None
        self._running = False
        self._on_ready = False
        self._event:dict[str,Callable[... , Awaitable]] = {}

    async def _event_monitoring(self): #Edit required
        self._call_event("on_ready")
        while self._running:
            await asyncio.sleep(1)
            self._call_event("test")

    def _call_event(self,event_name:str,*arg):
        if not self._running:
            return
        if event_name == "on_ready":
            if self._on_ready:
                return
            else:
                self._on_ready = True
        _event = self._event.get(event_name,None)
        if _event is None:
            return
        a = _event(*arg)
        if isinstance(a,Awaitable):
            asyncio.create_task(a)

    def event(self,f:Callable[..., Awaitable],name:str|None=None):
        self._event[f.__name__ if name is None else name] = f

    def run(self) -> asyncio.Task:
        if not self._running:
            self._running = True
            self._on_ready = False
            self.task = asyncio.create_task(self._event_monitoring()) #イベントを開始。
        return self.task
        

    async def wait_on_ready(self) -> bool:
        while self._running and (not self._on_ready):
            await asyncio.sleep(0)
        return self._running


    def stop(self) -> Awaitable:
        self._running = False
        self._on_ready = False
        return self.task or common.do_nothing()

