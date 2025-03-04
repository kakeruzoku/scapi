# クラウド変数

ここではクラウド変数について説明します。

# クラウド変数

> **get_tw_cloud(project_id,clientsession=None,*,purpose="unknown",contact="unknown",server_url:str="wss://clouddata.turbowarp.org")** `-> TurboWarpCloud`

**入力**
- **project_id** (`int|str`) プロジェクトID
- **clientsession** (`ClientSession|None`) 接続に使用したいClientSession。Noneの場合自動的に作成され、close()で閉じます。
- **purpose** (`str`) 利用する理由。例えば:``

## _BaseCloud

クラウド変数と通信するためのAPI。このページにあるクラスほぼすべてが継承しています。

> with ... as ...

自動的にconnect()とclose()を行います。

> **url** `-> str`

> property **header** `-> dict`

> **username** `-> str`

> **project_id** `-> int`

> **max_length** `-> int`

> **clientsession** `-> ClientSession`

> property **websocket** `-> aiohttp.ClientWebSocketResponse|None`

> property **is_connect** `-> bool`

接続が確立されているか

> await **connect(self,timeout=10)** `-> asyncio.Task`

**入力**
- **timeout** (`int`) 接続時のタイムアウトまでの秒数

クラウドサーバーに接続します(自動再接続機能付き)

> await **close(is_clientsession_close=None)**

**入力**
- **is_clientsession_close** (`bool|None`) ClientSessionをcloseするか Noneの場合、自動です。

> **get_vars()** `-> dict[int|float]`

クラウド変数の値を取得する。

> **get_var(self,variable)** -> `int|float|None`

**入力**
- **variable** (`str`) 変数名

入力した変数名に入っている値を返します。

> **set_var(self,variable,value,_wait=20)**

**入力**
- **variable** (`str`) 変更したい変数名 先頭に`☁ `がない場合は追加されます。
- **value** (`str|float|int`) 値
- **_wait** (`int`) 最大待機時間(秒)。接続が確立される前に時間が過ぎると`TimeoutError`が送出されます。

> **set_vars(self,data:,_wait:int=20)**

**入力**
- **data** (`dict[str,str|float|int]`) 変更したい変数名と値のペア 先頭に`☁ `がない場合は追加されます。
- **_wait** (`int`) 最大待機時間(秒)。接続が確立される前に時間が過ぎると`TimeoutError`が送出されます。

> **event** `-> CloudEvent`

このクラウド変数からクラウドイベントを作成します。

## TurboWarpCloud

ターボワープのクラウド変数を表します。追加の情報はありません。

# クラウドイベント

ここから下のクラスは`_BaseEvent`を継承しています。

## CloudEvent

> **cloud** `-> _BaseCloud`

接続に使用しているクラウドクラスを返す。

### event

> on_ready()

クラウドに接続して接続が完了した

> on_connect()

クラウド変数に接続した

> on_disconnect()

クラウド変数変数から(予期せず)接続されたり、接続に失敗した

> on_set(variable,value) 

**出力**
- **variable** (`str`) 変更された変数名
- **value** (`float|int`) 変更された値

値が変更された時

