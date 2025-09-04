from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from typing import Any, Awaitable, Callable, Coroutine, Generic, Literal, NoReturn, ParamSpec, TypeVar
from ..utils.common import do_nothing

async_def_type = Callable[..., Coroutine[Any,Any,Any]]
_CT = TypeVar("_CT", bound=async_def_type)
_P = ParamSpec('_P')

class _BaseEvent(ABC):
    """
    イベントのベースクラス。
    """
    def __init__(self):
        self._task:asyncio.Task|None = None
        self._event:asyncio.Event = asyncio.Event()
        self._on_ready = False

    def event(self,func:_CT) -> _CT:
        """
        イベントを追加するデコレータ。

        .. code-block:: python

            @event.event
            async def on_ready():
                print("ready!")

        クラスを継承することでもイベントを追加できます。

        .. code-block:: python

            class MyEvent(_BaseEvent):
                async def on_ready(self):
                    print("ready!")
        
        
        Args:
            func (_CT): 追加したい関数

        Raises:
            TypeError: コルーチン関数(async defで定義された関数)ではない
            ValueError: 関数名が`on_`から始まっていない。
        """
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Enter the async def function")
        if not func.__name__.startswith("on_"):
            raise ValueError("Enter the function name beginning with on_")
        
        setattr(self,func.__name__,func)
        return func
    
    
    def _call_event(self,func:Callable[_P,Coroutine[Any,Any,Any]],*args:_P.args,**kwargs:_P.kwargs):
        if self.is_running:
            asyncio.create_task(func(*args,**kwargs))
    
    async def _middleware(self,event:asyncio.Event):
        try:
            await self._event_monitoring(event)
        except asyncio.CancelledError:
            pass
        finally:
            await self._cleanup()
    
    
    @abstractmethod
    async def _event_monitoring(self,event:asyncio.Event) -> NoReturn:
        ...

    async def _cleanup(self):
        pass

    async def _wait(self):
        await self._event.wait()

    async def on_error(self,error:Exception):
        """
        [イベント] イベントモニター関数内でエラーが発生した。

        Args:
            error (Exception): 発生したエラー
        """
        pass


    @property
    def is_running(self) -> bool:
        """
        実行中かつポーズしていないか。

        Returns:
            bool
        """
        return self._task is not None and self._event.is_set()

    def run(self) -> asyncio.Task:
        """
        イベントの監視を開始する。

        Raises:
            ValueError: 既に開始済みです。 stop() するか、 resume() の使用を検討してください。

        Returns:
            asyncio.Task: 監視のタスク。await run()で監視が終了するまで(つまりstop()が実行されて終了処理が終わるまで)待ちます。
        """
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
        """
        監視を一時停止する。

        イベントが送出されなくなりますが、接続の維持のためにバックグラウンドで処理が続行される可能性があります。
        """
        self._event.clear()

    def resume(self):
        """
        監視を再開する。
        """
        self._event.set()

    def stop(self) -> asyncio.Task:
        """
        監視を終了する。

        Raises:
            ValueError: 実行中のタスクが見つからない

        Returns:
            asyncio.Task: 終了処理を含んだ監視のタスク
        """
        if self._task is None:
            raise ValueError("The event has already ended")
        task = self._task
        self._task = None
        task.cancel()
        return task
    
    async def __aenter__(self):
        self.run()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()