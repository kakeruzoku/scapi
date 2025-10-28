ユーティリティ
==============

.. contents::
    :depth: 3

定数
----

.. autodata:: scapi.UNKNOWN

.. warning::
    変数に ``UNKNOWN`` が入っているか確認したい場合は、必ず ``is`` を使用してください。
    ``==`` を使用した場合内容を問わず ``False`` を返すようになっているため、正確に判断できません。

.. autodata:: scapi.UNKNOWN_TYPE

ユーティリティクラス
--------------------

.. autoclass:: scapi.utils.common._AwaitableContextManager

.. autoclass:: scapi.File

クライアント
------------

.. autoclass:: scapi.HTTPClient

.. autoclass:: scapi.Response

.. autofunction:: scapi.create_HTTPClient_async