import asyncio
import datetime
from ..sites import user,project,studio,comment
from . import _base

class CommentEvent(_base._BaseEvent):
    def __init__(self,place:project.Project|studio.Studio|user.User,interval):
        self.place = place
        self.lastest_comment_dt = datetime.datetime.now(tz=datetime.timezone.utc)
        super().__init__(interval)

    async def _event_monitoring(self):
        self._call_event("on_ready")
        while self._running:
            comment_list = [i async for i in self.place.get_comments()]
            comment_list.reverse()
            temp_lastest_dt = self.lastest_comment_dt
            for i in comment_list:
                if i.sent_dt > self.lastest_comment_dt:
                    temp_lastest_dt = i.sent_dt
                    self._call_event("on_comment",i)
                self.lastest_comment_dt = temp_lastest_dt
            await asyncio.sleep(self.interval)