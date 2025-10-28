インストール
============

.. contents::
    :depth: 3

Scapiのインストール
-------------------

コマンドプロンプトなどのコンソール上で以下のコマンドを実行してください:

.. code-block::

    pip install scapi

Scapiが正しくインストールされたかは、IDLE等で以下のコードを実行します。

.. code-block:: py

    >>> import scapi
    >>> scapi.__version__
    ... '3.1.0'

この時帰ってきた文字列が、ダウンロードされたScapiのバージョンです。

Scapiのアップデート
-------------------

新たなバージョンがリリースされた場合は以下のコマンドを実行してください:

.. code-block::

    pip install scapi -U

``-U`` というオプションは既にインストールされていても最新版をインストールするオプションです。

バージョンを確認してみると最新版のバージョンが表示されるはずです。

.. code-block:: py

    >>> import scapi
    >>> scapi.__version__
    ... '3.1.1'

ソースコード
------------

Scapiのソースコードは常に `Github <https://github.com/kakeruzoku/scapi>`_ 上で公開されています。
