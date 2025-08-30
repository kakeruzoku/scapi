from abc import ABC, abstractmethod
import asyncio
from typing import Any, Awaitable, Callable, Coroutine, Generic, Literal, NoReturn, TypeVar
from ..utils import common

async_def_type = Callable[..., Coroutine[Any,Any,Any]]
_CT = TypeVar("_CT", bound=async_def_type)

class _BaseEvent(ABC):
    """_summary_

    _extended_summary_

    Attributes:
        ABC (_type_): _description_
    """
    def __init__(self):
        self._task:asyncio.Task|None = None
        self._event:asyncio.Event = asyncio.Event()
        self._on_ready = False

    def event(self,func:_CT) -> _CT:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Enter the async def function")
        if not func.__name__.startswith("on_"):
            raise ValueError("Enter the function name beginning with on_")
        
        setattr(self,func.__name__,func)
        return func
    
    
    def _call_event(self,name:str,*args) -> asyncio.Task[Any]:
        func:async_def_type = getattr(self,name)
        return asyncio.create_task(func(*args))
    
    async def _middleware(self,event:asyncio.Event):
        try:
            await self._event_monitoring(event)
        except asyncio.CancelledError:
            pass
        finally:
            await self._cleanup()
    
    
    @abstractmethod
    async def _event_monitoring(self,event:asyncio.Event) -> NoReturn:
        self._call_event("on_ready")
        while True:
            await asyncio.sleep(0)

    async def _cleanup(self):
        pass

    async def _wait(self):
        await self._event.wait()

    
    async def on_ready(self):
        pass


    def run(self) -> asyncio.Task:
        if self._task is not None:
            raise ValueError("The event has already started")
        self._event.set()
        self._task = asyncio.create_task(self._middleware(self._event))
        return self._task
    
    async def _asyncio_run(self):
        await self.run()
    
    def asyncio_run(self):
        asyncio.run(self._asyncio_run())
    
    def pause(self):
        self._event.clear()

    def resume(self):
        self._event.set()

    def stop(self) -> Awaitable:
        if self._task is None:
            return common.do_nothing()
        self._task.cancel()
        return self._task