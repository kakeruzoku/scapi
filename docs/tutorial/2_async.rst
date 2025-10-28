非同期処理
==========

Scapiでは非同期処理を採用してコードが書かれています。

非同期処理とは?
---------------

**制作中...**

.. _use_ipython:

対話形式でScapiを使用する
-------------------------

Scapiは非同期処理を採用しているため、Python標準の対話型シェルでは直接 ``await`` 式を簡単に使用することができません。
そのため、対話形式でScapiを試す場合は、 ``await`` 式をサポートする `iPython <https://ipython.org/>`_ のようなシェルの使用をおすすめします。
iPythonは ``pip install ipython`` でインストールでき、コンソールで ``ipython`` と入力することで起動できます。

iPython上で |HTTPClient| を ``await`` 式なしに作成する際は、 :func:`scapi.create_HTTPClient_async` を使用してください。これは、内部で使用しているaiohttpがイベントループを必要とするためです。

例えば以下のように使用できます。

.. code-block:: Python

    > ipython
    Python 3.13.5 ...

    In [1]: import scapi

    In [2]: u = await scapi.get_user("-25kakeru-25")

    In [3]: print(u)
    <User username:-25kakeru-25 id:96642364 session:None>

    In [4]: await u.client_close()

    In [5]: exit()

Next: :doc:`はじめてのScapi <3_first-scapi>`