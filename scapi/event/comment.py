import asyncio
import datetime
from enum import Enum
from typing import TYPE_CHECKING
from ..sites import user,project,studio,comment,activity
from . import _base

if TYPE_CHECKING:
    from ..sites.session import Session

class CommentEvent(_base._BaseEvent):

    def __repr__(self) -> str:
        return f"<CommentEvent place:{self.place} running:{self._running} event:{self._event.keys()}>"

    def __init__(self,place:project.Project|studio.Studio|user.User,interval):
        self.place = place
        self.lastest_comment_dt:datetime.datetime = datetime.datetime(2000,1,1,tzinfo=datetime.timezone.utc)
        super().__init__(interval)

    async def _event_monitoring(self):
        comments = [comment async for comment in self.place.get_comments()]
        if comments:  # コメントが存在する場合のみ処理
            self.lastest_comment_dt = comments[0].sent
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