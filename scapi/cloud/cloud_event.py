import asyncio
from typing import TYPE_CHECKING, AsyncGenerator
import warnings
from . import cloud
from ..event import _base
from ..sites import activity, base
from ..others import common
import datetime

if TYPE_CHECKING:
    from ..sites import project,session

async def _on_event(_self:"cloud._BaseCloud",method:str,variable:str,value:str,other:dict={}):
    cloud_activity = activity.CloudActivity(_self.clientsession,{
        "method":method,
        "name":variable,
        "value":value,
        "project_id":_self.project_id,
        "cloud":_self,
        "connection":_self,
        "datetime":datetime.datetime.now(tz=datetime.timezone.utc)
    })
    _self._event._call_event(f"on_{method}",cloud_activity)

async def _on_connect(_self:"cloud._BaseCloud"):
    _self._event._call_event(f"on_connect")
    _self._event._call_event(f"on_ready")

async def _on_disconnect(_self:"cloud._BaseCloud",interval:int):
    _self._event._call_event(f"on_disconnect",interval)


class CloudWebsocketEvent(_base._BaseEvent):
    def __repr__(self) -> str:
        return f"<CloudWebsocketEvent cloud:{self.cloud} running:{self._running} event:{self._event.keys()}>"

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
    
CloudEvent = CloudWebsocketEvent

class CloudLogEvent(_base._BaseEvent):
    def __init__(self,project_id:int,ClientSession:common.ClientSession|None=None,interval:float=1):
        super().__init__(interval)
        self.project_id:int = project_id
        self.ClientSession:common.ClientSession = common.create_ClientSession(ClientSession)
        self.lastest_dt:datetime.datetime  = datetime.datetime(2000,1,1,tzinfo=datetime.timezone.utc)
        self.Session:"session.Session|None" = None

    async def _event_monitoring(self):
        logs = [log async for log in self._get_logs(limit=1)]
        if logs:  # ログが存在する場合のみ処理
            self.lastest_dt = logs[0].datetime
        self._call_event("on_ready")
        while self._running:
            try:
                cloud_log_list = [i async for i in self._get_logs(limit=100)]
                cloud_log_list.reverse()
                temp_lastest_dt = self.lastest_dt
                for i in cloud_log_list:
                    if i.datetime > self.lastest_dt:
                        temp_lastest_dt = i.datetime
                        self._call_event(f"on_{i.method}",i)
                    self.lastest_dt = temp_lastest_dt
            except Exception as e:
                print(e)
                self._call_event("on_error",e)

            await asyncio.sleep(self.interval)

    def _get_logs(self,limit:int=100,offset:int=0) -> AsyncGenerator[activity.CloudActivity, None]:
        return base.get_object_iterator(
            self.ClientSession,f"https://clouddata.scratch.mit.edu/logs",
            None,activity.CloudActivity,self.Session,
            limit=limit,offset=offset,max_limit=100,add_params={"projectid":self.project_id},
            custom_func=base._cloud_activity_iterator_func,others={"project_id":self.project_id}
        )
