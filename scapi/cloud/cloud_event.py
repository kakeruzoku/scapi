import asyncio
import warnings
from . import cloud
from ..event import _base

async def _on_event(self:"cloud._BaseCloud",method:str,variable:str,value:float|int,other:dict={}):
    self._event._call_event(f"on_{method}",variable,value)


class CloudEvent(_base._BaseEvent):
    def __str__(self) -> str:
        return f"<CloudEvent cloud:{self.cloud} running:{self._running} event:{self._event.keys()}>"

    def __init__(self,cloud_obj:cloud._BaseCloud,reconnection_count:int|None=10):
        super().__init__(0)
        self.cloud:cloud._BaseCloud = cloud_obj
        self.reconnection_count:int|None = reconnection_count
        self.cloud._on_event = _on_event
        self.cloud._event = self

    async def _event_monitoring(self):
        tasks = await self.cloud.connect()
        while True:
            await tasks
            if not self._running:
                break
            self._call_event("on_disconnect",None)
            await self.cloud.close(False)
            await asyncio.sleep(1)
            c = 0
            while self.reconnection_count is None or c < self.reconnection_count:
                try:
                    tasks = await self.cloud.connect()
                except Exception as e:
                    await self.cloud.close(False)
                    self._call_event("on_disconnect",e)
                    await asyncio.sleep(10)
                    c = c + 1
                    continue
                break
            if c < self.reconnection_count:
                continue
            else:
                break
        
        self._call_event("on_close")
        await self.cloud.close()

    def stop(self):
        super().stop()
        asyncio.create_task(self.cloud.close(False))


