import asyncio
import datetime
from typing import TYPE_CHECKING
from ..sites import user
from . import _base

if TYPE_CHECKING:
    from ..sites.session import Session

class MessageEvent(_base._BaseEvent):

    def __str__(self) -> str:
        return f"<MessageEvent user:{self.user} running:{self._running} event:{self._event.keys()}>"

    def __init__(self,users:user.User,interval):
        self.user = users
        self.lastest_count = 0
        super().__init__(interval)

    async def _event_monitoring(self):
        self._call_event("on_ready")
        while self._running:
            now_count = await self.user.message_count()
            if now_count is None:
                self._call_event("on_failure")
            else:
                if self.lastest_count != now_count:
                    self._call_event("on_change",self.lastest_count,now_count)
                    self.lastest_count = now_count
            await asyncio.sleep(self.interval)

class SessionMessageEvent(_base._BaseEvent):

    def __str__(self) -> str:
        return f"<SessionMessageEvent session:{self.session} running:{self._running} event:{self._event.keys()}>"

    def __init__(self,sessions:"Session",interval):
        self.session = sessions
        self.lastest_dt = datetime.datetime.now(tz=datetime.timezone.utc)
        super().__init__(interval)

    async def _event_monitoring(self):
        self._call_event("on_ready")
        while self._running:
            comment_list = [i async for i in self.session.message()]
            comment_list.reverse()
            temp_lastest_dt = self.lastest_dt
            for i in comment_list:
                if i.datetime > self.lastest_dt:
                    temp_lastest_dt = i.datetime
                    self._call_event("on_activity",i)
                self.lastest_dt = temp_lastest_dt