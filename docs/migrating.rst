バージョン3への移行
===================

| Scapiバージョン3へようこそ！
| Scapiバージョン3は完全な書き直しが行われたため、バージョン2(v2.3.1以前)との互換性はほぼありません。
| このページでScapiを3.0.0に移行してください。

.. contents::
    :depth: 3

Scapiをアップデートする
-----------------------

コマンドプロンプトなどで ``pip install -U scapi`` と実行してください。

以下のコードで ``3.0.0`` 以降のバージョンが表示されれば成功です。

.. code-block:: python

    import scapi

    print(scapi.__version__) 

全体に関わる変更
----------------

完全な型ヒントサポート
^^^^^^^^^^^^^^^^^^^^^^

ないよー: (TODO)
- 全ての関数に対して返り値の型ヒントを付けた
- 内部処理でもレスポンスの内容に対して型ヒントを付与している

Unknownの追加
^^^^^^^^^^^^^

「不明」を表すデータ形式として |UNKNOWN| が追加されました。
UNKNOWNは==の比較で常に ``False`` を返します。

型ヒントとしてUNKNOWNを使いたい場合は :const:`UNKNOWN_TYPE <scapi.UNKNOWN_TYPE>` が使用できます。

.. code-block:: python

    import scapi

    unknown = scapi.UNKNOWN
    print(unknown == unknown) #False
    print(unknown is unknown) #True

    def hogehoge() -> scapi.UNKNOWN_TYPE:
        return unknown

個別の変更
----------

utils
^^^^^

- フォルダ名が ``other`` から ``utils`` に変更されました。

HTTPClient (旧ClientSession)
****************************

- 名前が ``ClientSession`` から |HTTPClient| に変更されました。
- ``aiohttp.ClientSession`` を継承しなくなり、 :attr:`<scapi.HTTPClient._session>` に移動されました。
- ``protect`` が削除され、その代わりに ``scratch_header`` と ``scratch_cookie`` が追加されました。

Response
********

- ``client`` の追加
- ``json()`` の引数の追加
  - ``loads``: json.loads の代わりに使用する関数
  - ``use_unknown`` ``dict.get()`` を使用した際の ``default`` 値のデフォルトを |UNKNOWN| にするか。これはNullとキーがない状態を区別するための機能です。

例外
****

一部の例外の名称が変更されました

================ ===================
旧               新                 
================ ===================
HTTPFetchError   |ProcessingError|
BadRequest       |ClientError|
HTTPNotFound     |NotFound|
BadResponse      |InvalidData|
================ ===================

- |Forbidden| / |CheckingFailed| の追加
- |IPBanned| / |AccountBrocked| / |CommentFailure| / |LoginFailure| は |Forbidden| を継承します
- ``ObjectFetchError`` 及び ``ObjectNotFound`` は削除されました

File
****
画像データなどの入力としてこのクラスが要求されることがあります。

**新機能**: ファイルパス/ファイルオブジェクト/バイナリ などから簡単にファイルを開けます。

詳しくは :class:`こちら <scapi.File>` を確認してください。

common
******

sites
^^^^^

Base
****

一部の属性の名称が変更されました

=================== =========================================================
旧                  新                 
=================== =========================================================
Session             :attr:`session <scapi._BaseSiteAPI.session>`
ClientSession       :attr:`client <scapi._BaseSiteAPI.client>`
session_closed      :attr:`client_closed <scapi._BaseSiteAPI.client_closed>`
session_close()     :func:`client_close() <scapi._BaseSiteAPI.client_close>`
=================== =========================================================

- 権限チェックは行わなくなり、 |Session| の有無のみ確認されます。
- ``link_session`` は削除されました。

- ``create_Partial_******`` は削除されました。代わりに直接クラスを呼び出して作成してください。

基本的には ``class( IDなどの識別情報 , HTTPClient/Session/None(空白でも可) )`` 形式で作成できます。

.. code-block:: python

    import scapi,asyncio

    async def run():
        async with scapi.HTTPClient() as client:
            user = scapi.User("-25kakeru-35",client)
            studio = scapi.Studio(35448485,client)
            project = scapi.Project(1188832070,client)

    asyncio.run(run())



session
*******
クラスが作成された際に自動的にアカウント情報を ``session_id`` からロードします。

一部の属性の名称が変更されました

=================== =========================================================
旧                  新                 
=================== =========================================================
=================== =========================================================



.. |IPBanned| replace:: :class:`IPBanned <scapi.exceptions.IPBanned>`
.. |AccountBrocked| replace:: :class:`AccountBrocked <scapi.exceptions.AccountBrocked>`
.. |Forbidden| replace:: :class:`Forbidden <scapi.exceptions.Forbidden>`
.. |CommentFailure| replace:: :class:`CommentFailure <scapi.exceptions.CommentFailure>`
.. |LoginFailure| replace:: :class:`LoginFailure <scapi.exceptions.LoginFailure>`
.. |CheckingFailed| replace:: :class:`CheckingFailed <scapi.exceptions.CheckingFailed>`
.. |ProcessingError| replace:: :class:`ProcessingError <scapi.exceptions.ProcessingError>`
.. |ClientError| replace:: :class:`ClientError <scapi.exceptions.ClientError>`
.. |NotFound| replace:: :class:`NotFound <scapi.exceptions.NotFound>`
.. |InvalidData| replace:: :class:`InvalidData <scapi.exceptions.InvalidData>`