はじめてのScapi
===============

.. note::
    このチュートリアルでは `IPython <https://ipython.org/>`_ を使用します。詳しくは :ref:`こちら <use_ipython>` を確認してください。

Scapiを使用する準備が整いました！まずは簡単なコードから実行してみましょう！

まずは IPython を起動してください。

.. code-block::

    > ipython

    In [1]:

まずはScapiをインポートしましょう。

.. code-block:: Python

    In [1]: import scapi

データを取得する
----------------

まずはプロジェクトを取得してみましょう。

Scratch上で公開されているプロジェクトを選んでみて下さい。この例では存在しないプロジェクトIDである ``0`` を使用しています。

プロジェクトを選んだら、プロジェクトIDを探しましょう。URLの ``https://scratch.mit.edu/projects/`` のあとに続く数字のことです。

まずは以下のようにコードを書いてみましょう。コード内の ``0`` の部分をあなたが選んだプロジェクトのIDに変更してみてください。

.. code-block:: Python

    In [2]: project = await scapi.get_project(0)

(プロジェクトが正常に共有されていて、Scratchサーバーとの通信に成功すれば、)エラーが発生せずに実行が完了します。

取得したプロジェクトを確認してみましょう。直接変数を表示する他に、様々な属性があります。

.. code-block:: Python

    In [3]: project
    Out[3]: <Project id:0 author:<User username:author id:0 session:None> session:None>

    In [4]: project.title
    Out[4]: 'title'

    In [5]: project.instructions
    Out[5]: 'instructions'

    In [6]: project.love_count
    Out[6]: 0

async forを使用する
-------------------

コメント欄やリミックス欄などの「リスト」的なデータを取得したい場合は ``async for`` 式を使用します。

.. code-block:: Python

    In [7]: async for comment in project.get_comments():
       ...:     print(comment)
       ...:
    <Comment id:0 content:content place:<Project id:0 author:<User username:author id:0 session:None> session:None> user:<User username:Commenter id:0 session:None> Session:None>
    <Comment id:0 content:content place:<Project id:0 author:<User username:author id:0 session:None> session:None> user:<User username:Commenter id:0 session:None> Session:None>
    ...
    <Comment id:0 content:content place:<Project id:0 author:<User username:author id:0 session:None> session:None> user:<User username:Commenter id:0 session:None> Session:None>

(コメントが投稿されている場合、)最大で40のコメントが表示されます。表示されない場合はコメントが投稿されているプロジェクトを選んで最初からやり直してみて下さい。

このような関数では、 ``limit`` (取得上限)や ``offset`` (開始位置)を指定することができます。指定しない場合、Scapi1回のリクエストで取得できる最大の量を取得しようとします。

.. code-block:: Python

    In [8]: async for comment in project.get_comments(limit=2,offset=10):
       ...:     print(comment)
       ...:
    <Comment id:0 content:content place:<Project id:0 author:<User username:author id:0 session:None> session:None> user:<User username:Commenter id:0 session:None> Session:None>
    <Comment id:0 content:content place:<Project id:0 author:<User username:author id:0 session:None> session:None> user:<User username:Commenter id:0 session:None> Session:None>

また、 ``limit`` を大きい数(通常 ``41`` 以上)指定した場合はScapiは自動的にリクエストを分割して処理します。その際に、全てのリクエストを行ってからではなく、毎回のリクエストごとに ``async for`` 文の中を実行します。