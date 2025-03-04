import asyncio
import datetime
from enum import Enum
from typing import TYPE_CHECKING
from ..sites import user,project,studio,comment,activity
from . import _base

if TYPE_CHECKING:
    from ..sites.session import Session

class CommentEvent(_base._BaseEvent):

    def __str__(self) -> str:
        return f"<CommentEvent place:{self.place} running:{self._running} event:{self._event.keys()}>"

    def __init__(self,place:project.Project|studio.Studio|user.User,interval):
        self.place = place
        self.lastest_comment_dt = datetime.datetime.now(tz=datetime.timezone.utc)
        super().__init__(interval)

    async def _event_monitoring(self):
        self._call_event("on_ready")
        while self._running:
            try:
                comment_list = [i async for i in self.place.get_comments()]
                comment_list.reverse()
                temp_lastest_dt = self.lastest_comment_dt
                for i in comment_list:
                    if i.sent_dt > self.lastest_comment_dt:
                        temp_lastest_dt = i.sent_dt
                        self._call_event("on_comment",i)
                    self.lastest_comment_dt = temp_lastest_dt
            except Exception as e:
                self._call_event("on_error",e)
            await asyncio.sleep(self.interval)