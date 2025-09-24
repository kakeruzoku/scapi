from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, AsyncGenerator, Iterable, Iterator, Literal
import aiohttp
import json
from .base import _BaseEvent
from ..utils.client import HTTPClient
from ..sites.activity import CloudActivity
from ..utils.types import (
    WSCloudActivityPayload
)
from ..utils.common import (
    __version__,
    api_iterative,
    wait_all_event
)

if TYPE_CHECKING:
    from ..sites.session import Session

class NormalDisconnection(Exception):
    pass

class _BaseCloud(_BaseEvent):
    """
    クラウドサーバーに接続するためのクラス。

    Attributes:
        url (str): 接続先のURL
        client (HTTPClient): 接続に使用するHTTPClient
        session (Session|None): Scratchのセッション
        header (dict[str,str]): ヘッダーに使用するデータ
        project_id (str|int): 接続先のプロジェクトID

    .. note::
        クラウド変数では、プロジェクトIDとして数字以外の文字列もサポートしています。
        プロジェクトIDがint|strとなっていることに注意してください。

    Attributes:
        username (str): 接続に使用するユーザー名
        ws_timeout (aiohttp.ClientWSTimeout): aiohttpライブラリのタイムアウト設定
        send_timeout (float): データを送信する時のタイムアウトまでの時間
    """
    max_length:int|None = None
    rate_limit:float|None = None

    def __init__(
            self,
            url:str,
            client:HTTPClient,
            project_id:int|str,
            username:str,
            ws_timeout:aiohttp.ClientWSTimeout|None=None,
            send_timeout:float|None=None
        ):
        super().__init__()
        self.url = url

        self.client:HTTPClient = client or HTTPClient()
        self.session:"Session|None" = None

        self._ws:aiohttp.ClientWebSocketResponse|None = None
        self._ws_event:asyncio.Event = asyncio.Event()
        self._ws_event.clear()

        self.header:dict[str,str] = {}
        self.project_id = project_id
        self.username = username

        self._send_queue:asyncio.PriorityQueue[tuple[int,int,tuple[asyncio.Future,int,str]]] = asyncio.PriorityQueue()
        self._send_next:tuple[asyncio.Future,int,str]|None = None
        self._count:int = 0

        self._data:dict[str,str] = {}

        self.ws_timeout = ws_timeout or aiohttp.ClientWSTimeout(ws_receive=None, ws_close=10.0) # pyright: ignore[reportCallIssue]
        self.send_timeout = send_timeout or 10

    @property
    def ws(self) -> aiohttp.ClientWebSocketResponse:
        """
        接続に使用しているWebsocketを返す

        Raises:
            ValueError: 現在接続していない。

        Returns:
            aiohttp.ClientWebSocketResponse
        """
        if self._ws is None:
            raise ValueError("Websocket is None")
        return self._ws
    
    def send(self,payload:list[dict[str,str]],*,project_id:str|int|None=None,priority:int=10) -> asyncio.Future:
        """
        サーバーにデータを送信する。

        Args:
            payload (list[dict[str,str]]): 送信したいデータ本体
            project_id (str | int | None, optional): 変更したい場合、送信先のプロジェクトID
            priority (int, optional): 送信の優先度。小さいほど優先され、初期値は10です。

        Returns:
            asyncio.Future: データの送信が完了するまで待つFuture
        """
        add_param = {
            "user":self.username,
            "project_id":str(self.project_id if project_id is None else project_id)
        }
        text = "".join([json.dumps(add_param|i)+"\n" for i in payload])
        future = asyncio.Future()
        self._count += 1
        self._send_queue.put_nowait((priority,self._count,(future,len(payload),text)))
        return future
    
    def queue_len(self) -> int:
        """
        キューの長さを取得する。

        Returns:
            int:
        """
        return self._send_queue.qsize()

    async def handshake(self):
        """
        ハンドシェイクを送信する
        """
        await self.ws.send_str(json.dumps({
            "method":"handshake",
            "user":self.username,
            "project_id":str(self.project_id)
        })+"\n")
        if self.rate_limit is not None:
            await asyncio.sleep(self.rate_limit)

    def _received_data(self,datas):
        if isinstance(datas,bytes):
            try:
                datas = datas.decode()
            except ValueError:
                return
        for raw_data in datas.split("\n"):
            try:
                data:WSCloudActivityPayload = json.loads(raw_data,parse_constant=str,parse_float=str,parse_int=str)
            except json.JSONDecodeError:
                continue
            if not isinstance(data,dict):
                continue
            method = data.get("method","")
            if method != "set":
                continue
            self._data[data.get("name")] = data.get("value")
            self._call_event(self.on_set,CloudActivity._create_from_ws(data,self))

    async def _event_monitoring(self,event:asyncio.Event):
        await asyncio.gather(self._connecter(),self._sender(),self._reader())
        if TYPE_CHECKING: raise #NoReturn

    async def _cleanup(self):
        self.clear_queue()

    async def _connecter(self):
        wait_count = 0
        while True:
            try:
                async with self.client._session.ws_connect(
                    self.url,
                    headers=self.header,
                    timeout=self.ws_timeout,
                    proxy=self.client._proxy,
                    proxy_auth=self.client._proxy_auth
                ) as ws:
                    self._ws = ws
                    await self.handshake()
                    self._ws_event.set()
                    self._call_event(self.on_connect)
                    wait_count = 0
                    await asyncio.Future()
            except Exception as e:
                self._call_event(self.on_error,e)
            self._ws_event.clear()
            self._call_event(self.on_disconnect,wait_count)
            await asyncio.sleep(wait_count)
            wait_count += 2
            await self._event.wait()

    async def _reader(self):
        while True:
            try:
                async for w in self.ws:
                    match w.type:
                        case aiohttp.WSMsgType.ERROR:
                            raise w.data
                        case aiohttp.WSMsgType.TEXT:
                            ws_data:str = w.data
                        case aiohttp.WSMsgType.BINARY:
                            ws_data:str = w.data.decode()
                        case aiohttp.WSMsgType.CLOSED|aiohttp.WSMsgType.CLOSING|aiohttp.WSMsgType.CLOSE:
                            raise NormalDisconnection
                        case _:
                            continue
                    if not self.is_running:
                        continue
                    for raw_data in ws_data.split("\n"):
                        try:
                            data:WSCloudActivityPayload = json.loads(raw_data,parse_constant=str,parse_float=str,parse_int=str)
                        except json.JSONDecodeError:
                            continue
                        if not isinstance(data,dict):
                            continue
                        method = data.get("method","")
                        if method != "set":
                            continue
                        self._data[data.get("name")] = data.get("value")
                        self._call_event(self.on_set,CloudActivity._create_from_ws(data,self))
            except NormalDisconnection:
                pass
            except Exception as e:
                self._call_event(self.on_error,e)
            await wait_all_event(self._event,self._ws_event)

    async def _sender(self):
        self._send_next = None
        while True:
            send_count = 1
            try:
                if self._send_next is None:
                    _,_,self._send_next = await self._send_queue.get()
                if not all((self._event.is_set(),self._ws_event.is_set())):
                    raise NormalDisconnection
                await self.ws.send_str(self._send_next[2])
                self._send_next[0].set_result(None)
                send_count = self._send_next[1]
                self._send_next = None
            except NormalDisconnection:
                pass
            except Exception as e:
                self._call_event(self.on_error,e)
            if self.rate_limit is not None:
                await asyncio.sleep(self.rate_limit*(min(1,send_count)))
            await wait_all_event(self._event,self._ws_event)

    async def on_connect(self):
        """
        [イベント] サーバーに接続が完了した。
        """
        pass

    async def on_set(self,activity:CloudActivity):
        """
        [イベント] 変数の値が変更された。

        Args:
            activity (CloudActivity): 変更のアクティビティ
        """
        pass

    async def on_disconnect(self,interval:int):
        """
        [イベント] サーバーから切断された。

        Args:
            interval (int): 再接続するまでの時間
        """
        pass


    @staticmethod
    def add_cloud_symbol(text:str) -> str:
        """
        先頭に☁がない場合☁を先頭に挿入する。

        Args:
            text (str): 変換したいテキスト

        Returns:
            str: 変換されたテキスト
        """
        if not text.startswith("☁ "):
            return "☁ "+text
        return text

    def set_var(self,variable:str,value:Any,*,project_id:str|int|None=None,add_cloud_symbol:bool=True,priority:int=10):
        """
        クラウド変数を変更する。

        Args:
            variable (str): 設定したい変数名
            value (Any): 変数の値
            project_id (str | int | None, optional): 変更したい場合、送信先のプロジェクトID
            add_cloud_symbol (bool, optional): 自動的に先頭に☁をつけるか
            priority (int, optional): 送信の優先度。小さいほど優先され、初期値は10です。

        Returns:
            asyncio.Future: データの送信が完了するまで待つFuture
        """
        return self.send([{
            "method":"set",
            "name":self.add_cloud_symbol(variable) if add_cloud_symbol else variable,
            "value":str(value)
        }],project_id=project_id,priority=priority)

    def set_vars(self,data:dict[str,Any],*,project_id:str|int|None=None,add_cloud_symbol:bool=True,priority:int=10):
        """
        クラウド変数を変更する。

        Args:
            data (dict[str,Any]): 変数名と値のペア
            project_id (str | int | None, optional): 変更したい場合、送信先のプロジェクトID
            add_cloud_symbol (bool, optional): 自動的に先頭に☁をつけるか
            priority (int, optional): 送信の優先度。小さいほど優先され、初期値は10です。

        Returns:
            asyncio.Future: データの送信が完了するまで待つFuture
        """
        return self.send([{
            "method":"set",
            "name":self.add_cloud_symbol(k) if add_cloud_symbol else k,
            "value":str(v)
        } for k,v in data],project_id=project_id,priority=priority)

    def clear_queue(self):
        """
        待機中の送信処理を全てキャンセルする
        """
        try:
            while True:
                _,_,data = self._send_queue.get_nowait()
                data[0].set_exception(asyncio.CancelledError)
        except asyncio.QueueEmpty:
            pass

turbowarp_cloud_url = "wss://clouddata.turbowarp.org"
scratch_cloud_url = "wss://clouddata.scratch.mit.edu"

class TurboWarpCloud(_BaseCloud):
    """
    turbowarpクラウドサーバー用クラス
    """
    def __init__(
            self,
            client: HTTPClient,
            project_id:int|str,
            username:str="scapi",
            reason:str="Unknown",
            *,
            url:str=turbowarp_cloud_url,
            timeout:aiohttp.ClientWSTimeout|None=None,
            send_timeout:float|None=None
        ):
        """

        Args:
            client (HTTPClient): 接続に使用するHTTPクライアント
            project_id (int | str): 接続先のプロジェクトID
            username (str, optional): 接続に使用するユーザー名
            reason (str, optional): サーバー側に提供する接続する理由
            url (str, optional): 接続先URL。デフォルトはwss://clouddata.turbowarp.orgです
            timeout (aiohttp.ClientWSTimeout | None, optional): aiohttp側で使用するタイムアウト
            send_timeout (float | None, optional): set_var()などを実行してから、送信できるようになるまで待つ最大時間
        """
        super().__init__(url, client, project_id, username, timeout, send_timeout)

        self.header["User-Agent"] = f"Scapi/{__version__} ({reason})"

class ScratchCloud(_BaseCloud):
    max_length = 256
    rate_limit = 0.1
    """
    scratchクラウドサーバー用クラス
    """
    def __init__(
            self,
            session:"Session",
            project_id:int|str,
            *,
            timeout:aiohttp.ClientWSTimeout|None=None,
            send_timeout:float|None=None
        ):
        """

        Args:
            session (Session): 接続するアカウントのセッション
            project_id (int | str): 接続先のプロジェクトID
            timeout (aiohttp.ClientWSTimeout | None, optional): aiohttp側で使用するタイムアウト
            send_timeout (float | None, optional): set_var()などを実行してから、送信できるようになるまで待つ最大時間
        """
        super().__init__(scratch_cloud_url, session.client, project_id, session.username, timeout, send_timeout)
        self.session = session
        self.header = {
            "Cookie":f'scratchsessionsid="{self.session.session_id}";',
            "Origin":"https://scratch.mit.edu"
        }

    async def get_logs(self,limit:int|None=None,offset:int|None=None) -> AsyncGenerator["CloudActivity", None]:
        """
        クラウド変数のログを取得する。

        Args:
            limit (int|None, optional): 取得するログの数。初期値は100です。
            offset (int|None, optional): 取得するログの開始位置。初期値は0です。

        Yields:
            CloudActivity
        """
        async for _a in api_iterative(
            self.client,"https://clouddata.scratch.mit.edu/logs",
            limit=limit,offset=offset,max_limit=100,params={"projectid":self.project_id},
        ):
            yield CloudActivity._create_from_log(_a,self.project_id,self.session or self.client)