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

多くの例外の名称が変更されました

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

sites
^^^^^

Base
****

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