from __future__ import annotations
import asyncio
import datetime
import sys
from typing import TYPE_CHECKING, NoReturn

from .base import _BaseEvent

if TYPE_CHECKING:
    from ..sites.user import User
    from ..sites.studio import Studio
    from ..sites.project import Project
    from ..sites.comment import Comment

class CommentEvent(_BaseEvent):
    """
    コメントイベントクラス

    Attributes:
        place (User|Project|Studio): 監視する場所
        interval (int): コメントの更新間隔
        is_old (bool): 古いAPIから取得するか
    """
    def __init__(self,place:"User|Project|Studio",interval:int=30,is_old:bool=False):
        """

        Args:
            place (User|Project|Studio): 監視する場所
            interval (int, optional): コメントの更新間隔。デフォルトは30秒です。
            is_old (bool, optional): 古いAPIから取得するか。デフォルトはFalseです。
        """
        super().__init__()
        self.place = place
        self.interval = interval
        self.is_old = is_old

        self.lastest_comment_time:datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    async def _event_monitoring(self, event:asyncio.Event) -> NoReturn:
        while True:
            if self.is_old:
                func = self.place.get_comments_from_old
            else:
                func = self.place.get_comments
            try:
                comments = [c async for c in func()]
                comments.reverse()
                lastest_comment_time = self.lastest_comment_time
                for c in comments:
                    created_at = c.created_at
                    if created_at and created_at > self.lastest_comment_time:
                        self._call_event(self.on_comment,c)
                        if created_at > lastest_comment_time:
                            lastest_comment_time = created_at
                if lastest_comment_time > self.lastest_comment_time:
                    self.lastest_comment_time = lastest_comment_time
            except Exception as e:
                self._call_event(self.on_error,e)
            await asyncio.sleep(self.interval)
            await event.wait()

    async def on_comment(self,comment:"Comment"):
        """
        [イベント] コメントが送信された。

        Args:
            comment (Comment):
        """
        pass
