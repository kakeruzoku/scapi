# 更新履歴

Scapiの更新履歴です。1.0.0以前の更新履歴は[こちら](https://github.com/kakeruzoku/scapi/blob/main/changelog.md )

# 1.x.x
## 1.3.0
### 新機能
- Scratchのクラウド変数接続サポート
  - `ScratchCloud`の追加
  - `CloudLogEvent`の追加
  - `Session`や`Project`に`get_cloud`などの一部関数の追加
- 権限チェックを行うかの設定`_BaseSiteAPI.check`を追加
### 更新/修正
- `limit`で指定した数とは違う量のオブジェクトを返していた問題を修正
- `CloudActivity`に`datetime`が追加

## 1.2.0
### 新機能
- エラー`IPBANError`の追加
### 更新/修正
- `CloudServer`で`host`,`port`にNoneが設定できるように
- 無駄な`ClientSession`が作成されないように修正
- バイナリデータを取得した際にステータスチェックがうまくいかない問題を修正
- デバック用に残されていた一部の関数等を削除
- 一部の型ヒントを修正
- セッション情報が正しく他のクラスに引き継げていなかった問題を修正
- 旧APIでコメントを送信できる機能を追加
- スタジオ作成機能の追加

## 1.1.1
### 更新/修正
- クラウド
  - `timeout`が正しく設定されていなかった問題を修正。(`_BaseCloud.timeout`の追加)
  - 型ヒントの修正
- API
  - セッション情報が正しく他のクラスに引き継げていなかった問題を修正
  - `UserComment`の作成時にエラーが発生する問題を修正
  - `Studio`の一部の関数が実行されない問題を修正

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