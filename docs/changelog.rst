更新履歴
========

3.x.x
-----

3.1.4
^^^^^
- :class:`scapi.RemixTree` 関連の関数/クラスを非推奨化
- :attr:`scapi.count_api_iterative` を追加

3.1.3
^^^^^

- |User| のユーザー名(:attr:`scapi.User.username`)が入力依存である場合の問題を修正
- :attr:`scapi.User.lower_username`, :attr:`scapi.User.real_username` の追加
- :attr:`scapi.Project.download_url` の追加

3.1.2
^^^^^

- docs: :doc:`チュートリアル <tutorial/index>` を追加
- :func:`scapi.create_HTTPClient_async` の追加

3.1.1
^^^^^
- fix: AsyncGeneratorの引数が1つしかない型ヒントがある問題を修正

3.1.0
^^^^^
- :func:`scapi.ForumPost.get_source` の追加
- :func:`scapi.User.report` の追加

3.0.0
^^^^^
| 3.0.0では書き直しによる大規模な変更が行われました。
| 詳しくは :doc:`このページ <migrating>` を確認してください

それ以前の更新
--------------
| ``1.1.0 - 2.3.1`` の更新履歴は `旧ドキュメントへ <https://kakeruzoku.github.io/scapi/ja/update>`_
| ``0.0.1 - 1.0.0`` の更新履歴は `Githubへ <https://github.com/kakeruzoku/scapi/blob/v2/changelog.md>`_