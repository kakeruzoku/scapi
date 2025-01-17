import asyncio
from typing import Any, Awaitable, Callable

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
        self._running = False
        self._event:dict[str,Callable[... , Awaitable]] = {}

    async def _event_monitoring(self): #Edit required
        self._call_event("on_ready")
        while self._running:
            await asyncio.sleep(1)
            self._call_event("test")

    def _call_event(self,event_name:str,*arg):
        if not self._running:
            return
        _event = self._event.get(event_name,None)
        if _event is None:
            return
        a = _event(*arg)
        if isinstance(a,Awaitable):
            asyncio.create_task(a)

    def event(self,func:Callable[..., Awaitable],name:str|None=None):
        self._event[func.__name__ if name is None else name] = func

    def run(self,*, is_task=True):
        self._running = True
        if is_task:
            return asyncio.create_task(self._event_monitoring()) #イベントを開始。
        else:
            asyncio.run(self._event_monitoring())

    def stop(self):
        self._running = False

