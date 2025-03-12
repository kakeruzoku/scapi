# 更新履歴

Scapiの更新履歴です。1.0.0以前の更新履歴は[こちら](https://github.com/kakeruzoku/scapi/blob/main/changelog.md )

# 1.x.x
## 1.1.0
### 破壊的変更
- クラウド
  - クラウド変数の値は`str`で保存されるようになり、`_BaseCloud.get_var()`/`_BaseCloud.get_vars()` で変数の値は`str`を返すようになりました。
  - `CloudEvent`で、`on_set`などの値の更新イベントは`CloudActivity`を引数として渡すように、`on_disconnect`では`interval`を渡すようになりました。
### 新機能
- `CloudServer` クラウドサーバーをホスティングできるようになりました
- `CloudActivity` クラウド変数の更新イベントをまとめたクラス
- `is_allowed_username()` ユーザー名がScratch上で有効であるか確認する関数。

### 更新/修正
- 一部のクラウドサーバーとの通信で発生する可能性のある問題を修正
- `User.is_new_scratcher`がScratcherかを表すbool値を返す問題を修正。
- 一部の型ヒントの修正

### ドキュメントの更新
- `ja/update` を追加。