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
        self._event:dict[str,Callable[... , Awaitable[Any]]] = {}

    async def _event_monitoring(self): #Edit required
        self._call_event("on_ready")
        while self._running:
            await asyncio.sleep(1)
            self._call_event("test")

    async def _setting_response(self,respnse): #option edit
        pass

    async def _run_event(self,func:Awaitable):
        await self._setting_response(await func)

    def _call_event(self,event_name:str,*arg):
        _event = self._event.get(event_name,None)
        if _event is None:
            return
        asyncio.create_task(self._run_event(_event(*arg)))

    def event(self,func:Callable[[Any], Awaitable[Any]]):
        self._event[func.__name__] = func

    def run(self,*, is_task=True):
        self._running = True
        if is_task:
            return asyncio.create_task(self._event_monitoring()) #イベントを開始。
        else:
            asyncio.run(self._event_monitoring())

    def stop(self):
        self._running = False

