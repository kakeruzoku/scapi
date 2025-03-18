import websockets
import asyncio
import time
import json
import datetime
import random
import string
import re
from typing import Awaitable,TypeVar,Callable

_T = TypeVar("_T")

from ..event import _base
from ..others import error,common
from ..sites import user,activity

async def try_except(coro:Awaitable[_T]|Callable[...,_T],data:tuple[int,str],*param) -> _T:
    #実行してエラーはいたら通信閉じる
    try:
        if isinstance(coro,Awaitable): return await coro
        else: return coro(*param)
    except Exception:
        raise error._cscc(data[0],data[1])
    
class CloudServerConnection:

    def __str__(self):
        return f"<CloudServerConnection id:{self.project_id} user:{self.username} joined:{self.connected} closed:{self.closed} set_count:{self.count}>"

    def __init__(
        self,
        websocket:websockets.ServerConnection,server:"CloudServer",
        project_id:int|None,username:str|None
    ):
        self.id:str = "".join(random.choices(string.ascii_letters + string.digits,k=10))
        self.websocket:websockets.ServerConnection = websocket
        self.project_id:int|None = project_id
        self.username:str|None = username
        self.server:"CloudServer" = server

        self.count:int = 0
        self.last_update:float = time.time()
        self.connected:datetime.datetime = datetime.datetime.fromtimestamp(self.last_update)
        self.closed:bool = False

    async def kick(self,code:int=4005,reason:str=""):
        if not self.closed:
            await self.websocket.close(code,reason)
            self.server._call_event("on_leave",self,code,reason)
            self.server._connection.pop(self.id,None)
            self.closed = True

_strjson = dict[str,"_strjson"]|list["_strjson"]|str|bool|None

async def on_connection(websocket:websockets.ServerConnection):
    cloud:"CloudServer" = websocket.server.scapi
    connection = CloudServerConnection(websocket,cloud,None,None)
    cloud._call_event("on_connect",connection)
    try: #_handshake
        text = await try_except(websocket.recv(True),(4000,"Not str"))
        data = await try_except(json.loads,(4000,"Not json"),text)
        if not isinstance(data,dict): raise error._cscc(4000,"Not object")
        if data.get("method") != "handshake": 
            raise error._cscc(4000,"Not handshake method")
        if ("project_id" not in data) or (not isinstance(data["project_id"],str)) or (not data["project_id"].isdecimal()):
            raise error._cscc(4000,"project_id is not number")
        if ("user" not in data) or (not isinstance(data["user"],str)):
            raise error._cscc(4000,"user is not string")
        if not user.is_allowed_username(data["user"]):
            raise error._cscc(4002,"This username is not allowed")
        if (cloud.policy.project_list is not None) and (data["project_id"] not in cloud.policy.project_list):
            raise error._cscc(4004,"This project_id is not allowed")
    
        connection.project_id = int(data["project_id"])
        connection.username = data["user"]
        await cloud._add_connection(connection)
    except error._cscc as e:
        await connection.kick(e.code,e.reason);return
    except Exception:
        await connection.kick(4000,f"Unknown Server Error on handshake");return

    #ここで保存してあるデータを送信する
    clouddata = connection.server._clouddata.get(connection.project_id)
    if clouddata is not None:
        text = []
        for k,v in clouddata.items():
            text.append(json.dumps({
                "method":"set",
                "name":"☁ "+k,
                "value":v[1]
            }))
        await connection.websocket.send("\n".join(text))

    try:
        async for message in websocket:
            if not isinstance(message,str):
                continue
            now = time.time()
            is_seted = False
            for text in message.split("\n"):
                data:_strjson = json.loads(message,parse_float=str,parse_constant=str,parse_int=str)
                if not isinstance(data,dict):
                    continue
                if data.get("method") != "set":
                    continue #set以外未対応
                req_pid, req_user = data.get("project_id"),data.get("user")
                if not (isinstance(req_pid,str) and req_pid == str(connection.project_id) and\
                        isinstance(req_user,str) and req_user.lower() == connection.username.lower()):
                    continue #データが違う
                if not (isinstance(data.get("name"),str) and isinstance(data.get("value"),str)):
                    continue #データが違う
                rate_limit = connection.server.policy.rate_limit
                if rate_limit is not None and connection.last_update + rate_limit > now:
                    break #レートリミット
                if connection.server._set_var(connection.project_id,data.get("name"),data.get("value"),connection.id):
                    is_seted = True
                    connection.last_update = connection.last_update + (rate_limit or 0)
                    connection.count = connection.count + 1
            if is_seted:
                connection.last_update = now
    except error._cscc as e:
        await connection.kick(e.code,e.reason);return
    except websockets.exceptions.ConnectionClosed:
        await connection.kick(4000,f"connection closed");return
    except Exception as e:
        await connection.kick(4000,f"Unknown Server Error");return
    await connection.kick(4000,f"Unknown Server Error")

class CloudServerPolicy:
    def __init__(
        self,*,
        max_length:int|None=None,
        max_var:int|None=None,
        save_all:bool = True,

        retention_period:tuple[int|None,int|None] = (0,None),
        project_list:list[int]|None = None,
        rate_limit:float|None = None,
        transmission_interval:float = 0.1
    ):
        self.max_length:int|None = max_length

        self.max_var:int|None = max_var

        # 最終更新からの変数の有効期限(秒) 
        # 1つめ 100%保存する機関 None...2つめの値になる
        # 2つめ 完全に抹消する期間 None...永久
        # どちらも0の場合、保存されません。
        self.retention_period = retention_period
        
        # 変数の数が最大を超えても保存するか
        # Trueの場合、変数の数が超えた際にrp_shortを超えた変数をできるだけ削除します。
        self.save_all:bool = save_all
        self.project_list:list[int]|None = project_list

        self.rate_limit:float|None = rate_limit

        self.transmission_interval:float = transmission_interval

    @property
    def retention_period(self) -> tuple[int|None,int|None]:
        return self._retention_period
    
    @retention_period.setter
    def retention_period(self,data:tuple[int|None,int|None]):
        self._retention_period = data
        self._rp_short:int|None = data[0]
        self._rp_long:int|None = data[1]
        self._is_save:bool = not (self._rp_long == 0 and self._rp_short == 0)


class CloudServer(_base._BaseEvent):
    def __init__(
        self,
        host:str,
        port:int,
        policy:CloudServerPolicy|None=None,
        ClientSession:common.ClientSession|None=None,
    ):
        super().__init__(0)

        self.ClientSession:common.ClientSession = common.create_ClientSession(ClientSession)
        self.host:str = host
        self.port:int = port

        self.policy:CloudServerPolicy = policy or CloudServerPolicy()
        self._connection:dict[str,CloudServerConnection] = {}

        self._clouddata:dict[int,dict[str,tuple[float,str]]] = {}
        # {project_id:{var:(lastest_update,var)}}

        self._set_queue:dict[int,list[tuple[str,str,str]]] = {}
        # clientid var value

        self.server:websockets.Server|None = None

    async def _event_monitoring(self):
        async with websockets.serve(
            on_connection, self.host, self.port,
        ) as server:
            self.server = server
            self.server.scapi = self #ゴリ押し実装
            self._call_event("on_ready")
            while self._running:
                await asyncio.sleep(self.policy.transmission_interval)
                # クライアントに送信
                task = []
                for k,v in self._set_queue.items():
                    text:list[tuple[str,str]] = []
                    for i in v: #データ作成
                        text.append((json.dumps({
                            "method":"set",
                            "name":"☁ "+i[1],
                            "value":i[2]
                        }),i[0]))

                        # [("json raw data","clientid")]
                    
                    #送信リスト
                    client_list:list[CloudServerConnection] = [i for i in self.connection if i.project_id == k]

                    for i in client_list:
                        send_data:list[str] = []
                        for raw,clientid in text:
                            if clientid == i.id:
                                continue
                            send_data.append(raw)
                        if len(send_data) == 0: #データがないなら送らない
                            continue
                        task.append(asyncio.create_task(i.websocket.send("\n".join(send_data))))
                
                self._set_queue = {} #キューを削除
                try:
                    asyncio.gather(*task)
                except Exception:
                    pass

                #古い変数を削除
                if self.policy._rp_long is None:
                    continue

                t = time.time() - self.policy._rp_long
                
                for k1,v1 in self._clouddata.items():
                    for k,v in list(v1.items()):
                        if v[0] < t:
                            v1.pop(k,None)
                            #print(f"del {k1} {k}")

        
        self._call_event("on_close")

    @property
    def connection(self) -> list[CloudServerConnection]:
        return list(self._connection.values())
        
    async def _add_connection(self,connection:CloudServerConnection):
        self._connection[connection.id] = (connection)
        self._call_event("on_join",connection)

    def _check_var(self,value) -> bool:
        return re.fullmatch(r"\-?[1234567890]+(\.[1234567890]+)?",value) is not None
    
    async def set_var(self,project_id:int,variable:str,value:str) -> bool:
        return self._set_var(project_id,variable,value,"")

    def _set_var(self,id:int,variable:str,value:str,clientid:str) -> bool:
        if not variable.startswith("☁ "):
            return False
        variable = variable[2:]
        if (self.policy.max_length is not None)and(self.policy.max_length < len(value) or self.policy.max_length < len(variable)):
            return False
        elif not self._check_var(value):
            return False
        #print(len(list(self._clouddata.get(id,[]))))
        if not self.policy._is_save:
            self._send_set_event(id,variable,value,clientid)
            return True
        elif self._clouddata.get(id) is None: #データない
            self._clouddata[id] = {}
        elif self.policy.max_var is None: #上限ない
            pass
        elif len(self._clouddata[id]) < self.policy.max_var: #最大に達してない]
            pass
        elif self.policy._rp_short is None: #削除なし(longはバックグラウンドで確認)
            return False
        else:
            t = time.time() - self.policy._rp_short
            var_data:list[tuple[float, str]] = [(v[0],k) for k,v in self._clouddata[id].items()]
            var_data.sort() #古い順に並び替え

            for i in var_data:
                if i[0] < t: #保存時間こしてたら削除
                    self._clouddata[id].pop(i[1],None)
                    #print(f"del {id} {i[1]}")
                if len(self._clouddata[id]) < self.policy.max_var:
                    break

            if len(self._clouddata[id]) >= self.policy.max_var and (not self.policy.save_all):
                return False #上限
            
        self._clouddata[id][variable] = (time.time(),value)
        self._send_set_event(id,variable,value,clientid)
        return True

    def _send_set_event(self,id:int,variable:str,value:str,clientid:str):
        if self._set_queue.get(id) is None: 
            self._set_queue[id] = []
        self._set_queue[id].append((clientid,variable,value))#キューに追加
        conn = self._connection.get(clientid,None)
        data = {
            "method":"set",
            "name":variable,
            "value":value,
            "user":conn and conn.username,
            "project_id":conn and conn.project_id,
            "cloud":self,
            "connection":conn
        }
        cloud_activity = activity.CloudActivity(self.ClientSession,data)
        self._call_event("on_set",cloud_activity)

    def get_vars(self,project_id:int) -> dict[str, str]:
        data = self._clouddata.get(project_id) or {}
        r:dict[str,str] = {}
        for k,v in data.items():
            r[k] = v[1]
        return r
    
    def get_var(self,project_id:int,variable:str) -> str | None:
        return self.get_vars(project_id).get(variable)