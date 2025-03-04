import asyncio
import warnings
from . import cloud
from ..event import _base

async def _on_event(self:"cloud._BaseCloud",method:str,variable:str,value:float|int,other:dict={}):
    self._event._call_event(f"on_{method}",variable,value)

async def _on_connect(self:"cloud._BaseCloud"):
    self._event._call_event(f"on_connect")
    self._event._call_event(f"on_ready")

async def _on_disconnect(self:"cloud._BaseCloud"):
    self._event._call_event(f"on_disconnect")


class CloudEvent(_base._BaseEvent):
    def __str__(self) -> str:
        return f"<CloudEvent cloud:{self.cloud} running:{self._running} event:{self._event.keys()}>"

    def __init__(self,cloud_obj:cloud._BaseCloud):
        super().__init__(0)
        self.cloud:cloud._BaseCloud = cloud_obj
        self.cloud._on_event = _on_event
        self.cloud._on_connect = _on_connect
        self.cloud._on_disconnect = _on_disconnect
        self.cloud._event = self

    async def _event_monitoring(self):
        tasks = await self.cloud.connect()
        await tasks
        self._call_event("on_close")
        await self.cloud.close()

    def stop(self):
        asyncio.create_task(self.cloud.close())
        return super().stop()


