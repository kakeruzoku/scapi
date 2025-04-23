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

> **get_vars()** `-> dict[str]`

クラウド変数の値を取得する。

**`1.1.0`で更新** クラウドデータは`str`で保存されるようになりました。

> **get_var(self,variable)** -> `str|None`

**入力**
- **variable** (`str`) 変数名

入力した変数名に入っている値を返します。

**`1.1.0`で更新** クラウドデータは`str`で保存されるようになりました。

> **set_var(self,variable,value,*,project_id=None,_wait=None)**

**入力**
- **variable** (`str`) 変更したい変数名 先頭に`☁ `がない場合は追加されます。
- **value** (`str|float|int`) 値
- **project_id** (`int|None`) 変更先のプロジェクトID。`None`で接続しているプロジェクトに対してリクエストを行います。
- **_wait** (`int|None`) 最大待機時間(秒)。接続が確立される前に時間が過ぎると`TimeoutError`が送出されます。

**`1.2.0`で更新** `_wait`はNoneが指定できるようになり、その場合、timeout値が使用されます。

**`1.4.0`で更新** 引数`project_id`を追加しました。

> **set_vars(self,data,*,project_id=None,_wait:int=None)**

**入力**
- **data** (`dict[str,str|float|int]`) 変更したい変数名と値のペア。先頭に`☁ `がない場合は追加されます。
- **project_id** (`int|None`)
- **_wait** (`int|None`)

**`1.2.0`で更新** `_wait`はNoneが指定できるようになり、その場合、timeout値が使用されます。

**`1.4.0`で更新** 引数`project_id`を追加しました。

> **create_var(variable,value=0,*,project_id=None,_wait=None)**

**入力**
- **variable** (`str`) 作成したい変数名 先頭に`☁ `がない場合は追加されます。
- **value** (`str|float|int`) 設定したい初期値
- **project_id** (`int|None`)
- **_wait** (`int|None`)

**`1.4.0`で追加**

> **rename_var(self,old,new,project_id=None,_wait=None)**

**入力**
- **old** (`str`) 変更元の変数名 先頭に`☁ `がない場合は追加されます。
- **new** (`str`) 変更先の変数名 先頭に`☁ `がない場合は追加されます。
- **project_id** (`int|None`)
- **_wait** (`int|None`)

**`1.4.0`で追加**

> **delete_var(variable,*,project_id=None,_wait=None)**

**入力**
- **variable** (`str`) 削除したい変数名 先頭に`☁ `がない場合は追加されます。
- **project_id** (`int|None`)
- **_wait** (`int|None`)

**`1.4.0`で追加**

> **event** `-> CloudEvent`

このクラウド変数からクラウドイベントを作成します。

## ScratchCloud

**`1.3.0`で追加**

Scratchでのクラウド変数を表します。`_BaseCloud`を継承しています。

> **Session** `-> Session`

接続に使用するScratchアカウント。

> async for **get_logs(,limit=40,offset=0)** `-> CloudActivity`

ログAPIからログを読み込みます。

> **log_event(interval=1)** `-> CloudLogEvent`

**入力**
- **interval** (`float`) 更新間隔

## TurboWarpCloud

ターボワープのクラウド変数を表します。`_BaseCloud`を継承していて、追加の情報はありません。

# クラウドイベント

## CloudEvent

`_BaseEvent`を継承しています。

> **cloud** `-> _BaseCloud`

接続に使用しているクラウドクラスを返す。

### event

ここでの引数`cloud_activity`は`CloudActivity`です。

> on_ready()

クラウドに接続して接続が完了した

> on_connect()

クラウド変数に接続した

> on_disconnect(interval)

**出力**
- **interval** (`int`) 再接続する待機時間

クラウド変数変数から(予期せず)切断されたり、接続に失敗した

> on_set(cloud_activity) 

値が変更された時

**`1.1.0`で更新** データが`CloudActivity`でまとまって出力されるようになりました。


## CloudLogEvent

**`1.3.0`で追加**

Scratchのクラウド変数ログAPIを使用したイベント。`_BaseEvent`を継承しています。

> **project_id** `-> int`

> **ClientSession** `-> ClientSession`

> **lastest_dt** `-> datetime.datetime`

> **Session** `-> Session`

### event

ここでの引数`cloud_activity`は`CloudActivity`です。

通常のイベントとの違い

- 変数を変更したユーザーを取得可能
- `on_create` `on_rename` `on_del` が利用可能

> on_ready()

> on_set(cloud_activity) 

**出力**
- **cloud_activity** (`CloudActivity`)

# クラウドサーバー

クラウドサーバーをホスティングできます。

## CloudServer

> scapi.**CloudServer(host=None,port=None,policy=None,ClientSession=None)**

**入力**
- **host** (`str|None`) ホスト先IP
- **port** (`int|None`) 使用したいポート
- **policy** (`CloudServerPolicy|None`) サーバーのポリシー(設定)

クラウドサーバーを表すクラス。 `_BaseEvent`を継承しています。

> **host** `-> str|None`

> **port** `-> int|None`

**`1.2.0`で更新** Noneも指定できるように変更

> **policy** `-> CloudServerPolicy`

> **server** `-> websockets.Server`

> property **connection** `-> list[CloudServerConnection]`

クラウドサーバーに接続しているセッションのリスト

> **set_var(project_id,variable,value)** `-> bool`

**入力**
- **project_id** (`int`) 変更先のプロジェクトID
- **variable** (`str`) 変数名
- **value** (`str`) 変数の値

変数を更新します。成功した場合`True`が返されます。

> **get_vars(project_id)** `-> dict[str,str]`

**入力**
- **project_id** (`int`) プロジェクトID

> **get_var(project_id,variable)** `-> str|None`

**入力**
- **project_id** (`int`) プロジェクトID
- **variable** (`str`) 変数名

## CloudServerPolicy

> scapi.**CloudServerPolicy(max_length=None,max_var=None,save_all=True,retention_period=(0,None),project_list=None,rate_limit=None,transmission_interval=0.1)**

**入力**
- **max_length** (`int|None`) 変数と値の最大文字数
- **max_var** (`int|None`) 1プロジェクトあたりの最大変数数
- **save_all** (`bool`) 変数の最大数を越してもできるだけ保存する。
- **retention_period** (`tuple[int|None,int|None]`) 変数の保存ポリシー。(0,0)で一切データがが保存されないモードになります。
  - 1つめ ... 変数のデータを100%残す時間(s)
  - 2つめ ... 変数のデータを100%抹消する時間(s) (優先順位高)
- **project_list** (`list[int]|None`) 接続を許可するプロジェクトIDのリスト
- **rate_limit** (`float|None`) 変数の更新をするレート制限。1つの変数の更新ごとに適用されます。
- **transmission_interval** (`float`) クライアントにデータの更新を送信する間隔。

サーバーの設定を示すクラス

## CloudServerConnection

クライアントの接続を表すクラス。

> **id** `-> str`

Scapi側が勝手に生成したID。識別に使われます。

> **websocket** `-> websockets.ServerConnection`

> **project_id** `-> int`

> **username** `-> str`

> **server** `-> CloudServer`

> **count** `-> int`

変数を更新した回数

> **last_update** `-> float`

変数を最終更新した時間。(time.time()の値)

> **connected** `-> datetime.datetime`

クライアントが接続した時間。

# 例外
- `CloudError` クラウド変数に関連したエラー(基本下のクラスの例外がでる)
  - `CloudConnectionFailed` クラウド変数への接続に失敗した(またはタイムアウトした)