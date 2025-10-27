from abc import abstractmethod
import asyncio
import datetime
from typing import TYPE_CHECKING, AsyncGenerator, Callable, Generic, NoReturn,TypeVar

from scapi.sites.activity import Activity
from .base import _BaseEvent
from ..utils.common import UNKNOWN_TYPE

if TYPE_CHECKING:
    from ..sites.user import User
    from ..sites.studio import Studio
    from ..sites.project import Project
    from ..sites.comment import Comment
    from ..sites.activity import Activity
    from ..sites.session import Session

_T = TypeVar("_T")


class _TemporalEvent(_BaseEvent,Generic[_T]):
    """
    一定期間ごとにリストを取得して新着のものをイベントとして送出するタイプのイベントの共通関数

    Attributes:
        interval (float): 更新間隔
        lastest_time (datetime.datetime): 確認したイベントの最後の時間
    """
    def __init__(
            self,
            interval:float,
            check_func:Callable[[],AsyncGenerator[_T,None]],
            datetime_attr:str
        ):
        super().__init__()

        self.interval = interval
        self._check_func = check_func
        self._datetime_attr = datetime_attr
        self.lastest_time:datetime.datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    async def _event_monitoring(self, event: asyncio.Event) -> NoReturn:
        while True:
            try:
                objs = [c async for c in self._check_func()]
                objs.reverse()
                lastest_time = self.lastest_time
                for obj in objs:
                    created_at:datetime.datetime|None|UNKNOWN_TYPE = getattr(obj,self._datetime_attr)
                    if created_at and created_at > self.lastest_time:
                        self._make_event(obj)
                        if created_at > lastest_time:
                            lastest_time = created_at
                if lastest_time > self.lastest_time:
                    self.lastest_time = lastest_time
            except Exception as e:
                self._call_event(self.on_error,e)
            await asyncio.sleep(self.interval)
            await event.wait()

    @abstractmethod
    def _make_event(self,obj:_T):
        ...

class CommentEvent(_TemporalEvent["Comment"]):
    """
    コメントイベントクラス

    Attributes:
        place (User|Project|Studio): 監視する場所
        is_old (bool): 古いAPIから取得するか
    """
    def __init__(self,place:"User|Project|Studio",interval:int=30,is_old:bool=False):
        """

        Args:
            place (User|Project|Studio): 監視する場所
            interval (int, optional): コメントの更新間隔。デフォルトは30秒です。
            is_old (bool, optional): 古いAPIから取得するか。デフォルトはFalseです。
        """
        if is_old:
            super().__init__(interval,place.get_comments_from_old,"created_at")
        else:
            super().__init__(interval,place.get_comments,"created_at")
        
        self.place = place
        self.is_old = is_old

    def _make_event(self, obj:"Comment"):
        self._call_event(self.on_comment,obj)
    
    async def on_comment(self,comment:"Comment"):
        """
        [イベント] コメントが送信された。

        Args:
            comment (Comment):
        """
        pass

    '''
    イベントのデータは変更されるべきじゃない？

    @property
    def place(self) -> User|Project|Studio:
        """
        監視する場所

        Returns:
            User|Project|Studio:
        """
        return self._place

    @property
    def is_old(self) -> bool:
        """
        古いAPIから取得するか

        Returns:
            bool:
        """
        return self._is_old
    
    @is_old.setter
    def is_old(self,value:bool):
        self._is_old = value
        self._check_func = self._place.get_comments_from_old if value else self._place.get_comments

    @place.setter
    def place(self,value:User|Project|Studio):
        self._place = value
        self.is_old = self._is_old
    '''

class MessageEvent(_TemporalEvent["Activity"]):
    """
    メッセージイベントクラス

    Attributes:
        session (Session): メッセージを監視しているアカウント
    """
    def __init__(self,session:"Session",interval:float=30):
        super().__init__(interval,session.get_messages,"created_at")
        self.session = session

    def _make_event(self, obj:Activity):
        self._call_event(self.on_message,obj)

    async def on_message(self,message:Activity):
        """
        [イベント] メッセージを受信した。

        Args:
            message (Activity):
        """
        pass