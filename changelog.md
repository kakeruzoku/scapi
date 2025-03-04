# tag
- **[Del]** 機能の削除
- **[Change]** 仕様変更
- **[Fix]** 修正
- **[Add]** 追加
- **[Other]** その他
# 1.x.x
## 1.0.x
### 1.0.0
- **[Change]** 必要なパッケージを変更
- cloud
  - **[Del]** 使用されていないいくつかの属性を削除
  - **[Change]** headerをproperty化
  - **[Add]** 接続失敗時に`TimeoutError`を送出するように
  - **[Add]** `set_var`/`set_vers`でクラウドに接続されていない場合は接続されるまで待つように
- event
  - **[Add]** `wait_on_ready()`,`task`の追加
  - **[Change]** `try except`文で例外で終了しないように変更
- **[Del]** `BytesResponse`を削除して`Response`と統合
- **[Add]** 例外`CommentFailure`の追加
- **[Del]** `get_csrf_token_sync`の削除
- sites
  - **[Add]** `_BaseSiteAPI`で`async with ... as ...`文に対応
  - **[Add]** IDを指定する引数でオブジェクトの入力に対応
  - **[Fix]** 一部のActivityを修正
  - **[Change]** コメントでの引数`parent_id`,`commentee_id`を`parent`,`commentee`に変更
  - **[Add]** Project.downloadでアセットをダウンロードするかを追加/一部の問題を修正
  - **[Change]** `RemixTree`でデータの保存方法を変更し、メモリの使用量を削減
  - **[Fix]** Studio.Activityでデータがうまく取得できない問題を修正
  - **[Add]** Userでwebサイトから所属クラス情報を取得できるように(あと軽量化)
  - **[Fix]** その他微弱な修正や型ヒントの追加
- web
  - **[Add]** 新たにwebディレクトリを作成 wiki等の掲載を行います [こちら](https://scapi.kakeru.f5.si )から閲覧できます

# 0.x.x
## 0.6.x
### 0.6.2
- **[Change]** `_BaseCloud`に自動再接続機能を追加
- **[Fix]** そのた微弱な修正多数

### 0.6.1
2025/01/17更新
- **[Add]** クラウドイベントを作成
- **[Change]** Eventで非同期だけでなく同期も追加可能に
- **[Fix]** `obj != other` が `obj > other` となっていた問題を修正
- **[Change]** 一部関数で失敗すると `False`を返すのではなく、`ResponseError`を発生させるように。

### 0.6.0
2025/01/09更新
- **[Add]** クラウド変数に対応(ターボワープのみ)
- **[Change]** `check_usernames` `check_passwords`→`check_username` `check_password` 引数も変更
- **[Add]** 統計情報の取得API
- **[Add]** 翻訳 ttsAPIの追加
- **[Fix]** その他修正いろいろ


## 0.5.x
### 0.5.0
2025/01/05更新
- **[Add]** `check_usernames` `check_passwords`の追加
- **[Del]** `Activity`での`==`対応
- **[Add]** async forで取得できるデータを一括で高速に取得できる関数`get_list_data` `get_page_list_data`の追加
- **[Add]** メインページ関連のAPIの追加、`ScratchNews`クラス
- **[Add]** `RemixTree`の追加
- **[Change]** `Session.feed`→`Session.following_feed`
- **[Fix]** インストールすべきモジュールが全て入れられなかった問題を修正
- **[Add]** ほかのAPIで`ClientSession`が使えるように`create_custom_ClientSession`を追加

## 0.4.x
### 0.4.0
2025/01/03更新
- **[Add]** イベント機能の追加
  - CommentEvent,MessageEvent,SessionMessageEventの3つ作成する関数も追加
- **[Fix]** Activity,User,Studio,Session,Comment,Projectで修正
- **[Add]** Backpackの追加
- **[Add]** Userでアイコンを変更できるように



## 0.3.x
### 0.3.1
2024/12/31更新
- **[Add]** `Classroom`の追加
  - **[Add]** `get_classroom` `get_classroom_by_token` の追加
- Session
  - **[Add]** `my_classroom` `viewed_projects` `get_forumtopic` `get_forumpost` `explore_projects` `search_projects` `explore_studios` `search_studios` の追加
- **[Fix]** `Project.download()` がうまくいかない問題を修正


### 0.3.0
2024/12/31更新
- ClientSession関連
  - **[Add]** BytesResponseを追加してバイナリデータのリクエストに対応
  - **[Change]** ClientSessionをまとめた
- フォーラム関連
  - **[Add]** `ForumStatus` (ユーザーのフォーラムの活動情報クラス) の追加
  - **[Add]** `ForumPost` の追加
  - ForumTopic
    - **[Add]** `ForumTopic.get_posts()` の追加
  - **[Add]** `ForumPost` (投稿を表す) の追加
    - **[Add]** `scapi.get_post()` `create_Partial_ForumPost()` の追加`
- Project
  - **[Add]** `Project.download()` `love()` `favorite()` `view()` `edit()` `set_thumbnail()` `set_json()` の追加
- Studio
  - **[Add]**  `follow()` `set_thumbnail()` `edit()` `open_adding_project()` `open_comment()` `invite()` `accept_invite()` `promote()` `remove_user()` `transfer_ownership()` `leave()` `add_project()` `remove_project()` `projects()` `curators()` `managers()` `host()` `roles()` の追加
- User
  - **[Add]**  `toggle_comment()` `edit()` `follow()` の追加
- Session
  - **[Add]** `feed()` の追加
- Activity
  - **[Add]** `Session.feed()`に対応
  - **[Add]** `ActivityType`に`ProjectRemix`を追加
  


## 0.2.x
### 0.2.2
2024/12/27更新
- **[Fix]** IDでintで指定した場合にエラーが発生する問題を修正
- フォーラム関連
  - **[Add]** フォーラムのトピックを取得する関数 `get_topic_list` `get_topic_list` を追加
  - **[Add]** `ForumCategoryType`を追加
  - **[Add]** `ForumTopic`に`int(), ==,<,>,<=,>=`、その他複数のデータを追加

### 0.2.1 
2024/12/26更新
- **[Fix]** projectなどのIDが`int`ではなく`str`を返すように
- **[Add]** `project` `studio` `user` `Comment` に `int(), ==,<,>,<=,>=` に対応(IDで比べる)
- **[Fix]** `Activity`で `==`の追加,一部タイプのアクティビティでエラーが発生する問題を修正
- **[Add]** Readmeに情報を追加

### 0.2.0
2024/12/26更新
- **[Fix]** ログインで一定条件下で正しくログインできない問題を修正。
- **[Add]** 多くのクラスに`__str__`を追加
- **[Add]** `Activity`クラスの追加
  - 取得関数 `User.activity`,`Studio.activity`,`Session.message`
- **[Add]** `ForumTopic`クラスの追加(仮・update等未対応)
- **[Add]** `create_Partial_*****` に Session を追加できるように
- **[Add]** `create_Partial_Comment` を追加
- Session
  - **[Add]** `create_Partial_myself` の追加

## 0.1.x
### 0.1.0
- _BaseSiteAPI
  - **[Change]** `_BaseSiteAPI.has_session` を`@property`に変更、bool値を返すように。従来の関数は `_BaseSiteAPI.has_session_raise`
  - **[Change]** `_BaseSiteAPI.link_session`if_closeの初期値が`True`から`False`に
- **[Change]** クラス名変更 `Requests` -> `ClientSession`
  - **[Add]** `ClientSession.header` `ClientSession.cookie` (property/読み取り専用) の追加
- User
  - **[Add]** `await User.loves()` `await User.love_count()` の追加
  - **[Add]** `async for User.get_comment_by_id()`に引数`start`(初期値1)を追加
- UserComment
  - **[Add]** `UserComment.page` ユーザーコメントが何ページ目にあるか update()の際に活用されます。
- Session
  - **[Del]** `Session.new_scratcher`
  - **[Add]** `Session.scratcher`
  - **[Del]** `Session.is_valid` 未使用、需要ない

- **[Change]** 例外クラス `scapi.*****` から `scapi.exception.*****` に

## 0.0.x
### 0.0.3
- **[Fix]** setup.pyを修正

### 0.0.2
- **[Fix]** Importを修正

### 0.0.1
- **[Other]** 共有
- **[Add]** クラスの追加
  - Response
  - Requests
  - _BaseSiteAPI
  - Comment
  - UserComment
  - Project
  - SessionStatus
  - Session
  - Studio
  - User
  - その他!
- **[Add]** 関数の追加
  - ログイン(`login`/`session_login`)
  - データの取得(`get_*****`など)
  - 部分的なデータの作成(`create_Partial_*****`)
  - その他!