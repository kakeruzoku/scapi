# tag
- **[Del]** 機能の削除
- **[Change]** 仕様変更
- **[Fix]** 修正
- **[Add]** 追加
- **[Other]** その他

# 0.x.x
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