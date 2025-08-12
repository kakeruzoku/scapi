# 更新履歴

Scapiの更新履歴です。1.0.0以前の更新履歴は[こちら](https://github.com/kakeruzoku/scapi/blob/main/changelog.md )
# 2.x.x
## 2.3.1
- スタジオフォローのAPIが呼び出されていない問題を修正
- その他コードの最適化

## 2.3.0
### 新機能
- バックパックへのアップロード

### 更新/修正
- Python`3.11`以下に対応するための修正
- バックパック関連の関数やクラスが読み込まれていない問題を修正

## 2.2.0
### 破壊的変更
- 一部利用できない関数で`warning`ではなくエラー出すように変更
  - `ForumTopic._update_from_dict`
  - `ForumPost._update_from_dict`
  - `ScratchNews.update`
  - `RemixTree.update`

### 新機能
- 生徒アカウントをユーザー名だけで作成する機能の追加

### 更新/修正
- `CommentEvent`が非推奨関数を使用していた問題を修正
- コメントが正しく取得されない問題を修正
- その他微弱な修正


## 2.1.1
### 更新/修正
- import時に環境によって構文エラーが発生する問題を修正

## 2.1.0
### 新機能
- `Session.register_info()` 生徒アカウントでのアカウント情報登録に対応
- `ForumTopic.follow()` フォーラムのトピックのフォローに対応
- `ForumPost.report()` フォーラムの投稿の報告に対応
- `scapi.download_asset()`アセットのダウンロードに対応

### 更新/修正
- `Session.change_password()` パスワードリセット時のパスワード更新に対応
- `scapi.get_topic_list`関数のカテゴリー指定にカテゴリーIDとして`int`が使えるように変更
- 非推奨関数が正しく実行されない問題を修正
- `Comment.update()`関数での問題を修正
- その他微弱な修正

## 2.0.1
### 新機能
- ScratchのSessionIDからデータを取得
- `Studio.classroom()`関数を追加

### 更新/修正
- 一部の関数でセッション情報が引き継がれない問題を修正
- 多くのクラスに`__repr__`を追加(`__str__`と同じ値)

### その他
- ドキュメントページ`ja/quickstart` `migration`を追加

## 2.0.0
### 破壊的変更
- `*****NotFound`が削除され、`ObjectNotFound`に統一されました。
- Comment
  - `UserComment`が削除され、`User`に統一されました。
  - `sent_dt`は`sent`に変更されました。

### 新機能
- 教師アカウント関連のAPIの追加
  - `Classroom`
    - クラスの作成
    - クラスの編集機能の追加
    - クラススタジオの作成
    - 教師アカウント向けのクラス/アクティビティ/生徒/スタジオの取得
    - 生徒のパスワードの編集
  - `Activity`でクラスでの(教師向けの)アクティビティに対応
  - `User`
    - パスワードを変更(またはリセット)可能
- スタジオ・ユーザー・プロジェクトでの報告機能の追加
- Scratcher招待関連のAPIの追加
- 非推奨機能の通知

### 更新/修正
- Session
  - SessionIDでのログインが失敗する問題を修正
  - Sessionの更新時に新しくstatusクラスが作成されないように(`update`で更新されるように)修正
  - スタジオ作成時に`Studio`クラスに`Session`が入らない問題を修正
  - `get_mystuff_project` `get_mystuff_studio` をそれぞれ `get_mystuff_projects` `get_mystuff_studios`に変更
- 権限チェックを行うかの設定`_BaseSiteAPI.check`が`chack`になっていた問題を修正
- そのた微弱な(利用上の変更のない)修正

# 1.x.x
## 1.6.0
### 新機能
- `ScratchCloud.auto_event()` `CloudWebsocketEvent`と`CloudLogEvent`を自動的に選択します。

### 更新/修正
- デバック時に使用していた関するの削除忘れを修正
- `CloudEvent`が`CloudWebsocketEvent`に変更。(引き続き`CloudEvent`も使用できます。)


## 1.5.0
### 新機能
- 私の作品欄のAPIを追加
- アカウントの設定のAPIを追加
- アセットのアップロードの追加
### 更新/修正
- `set_var`などでの値チェックを削除しました。
- `Session`にそのアカウントの`User`オブジェクトがキャッシュされるようになりました。

## 1.4.0
### 新機能
- クラウド変数
  - `create` `rename` `delete`メソッド送信機能の追加
  - パケットごとにプロジェクトIDを指定できるように
- Scratch以外のサイトにsessionID等を送信しないようにする機能の追加(`ClientSession.protect`)
### 更新/修正
- `CloudActivity`で`set`メソッド以外にも対応
- `Activity`に`UserJoin`を追加
- メッセージ既読機能の追加

## 1.3.1
### 更新/修正
- [PR29](https://github.com/kakeruzoku/scapi/pull/29 ) イベントで、時間のずれによる問題を解消
- cookieに必要ない情報を削除

## 1.3.0
### 新機能
- Scratchのクラウド変数接続サポート
  - `ScratchCloud`の追加
  - `CloudLogEvent`の追加
  - `Session`や`Project`に`get_cloud`などの一部関数の追加
- 権限チェックを行うかの設定`_BaseSiteAPI.check`を追加
- ocularAPI
  - `OcularReactions`の追加
  - `OcularStatus`の追加
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