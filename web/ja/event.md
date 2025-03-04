# イベント

イベントについて説明します。

# 共通イベントクラス

## _BaseEvent

> **interval** `-> float`

データの更新間隔

> @event

イベントを登録します。`async def`を使用する必要があります。

> **run(is_task=True)** `-> asyncio.Task`

実行します。(awaitすると終了するまで待つ)

既に実行している場合は何も行われず、`asyncio.Task|None`が返されます。

> await **wait_on_ready()** `-> bool`

準備完了まで(**on_ready**)または終了するまで待ちます。

> **stop()** `-> Awaitable`

実行を停止します。(awaitすると終了するまで待つ)

### event

> on_ready()

準備が完了したら。`on_ready`は1回のみ呼び出されます。

> on_error()

イベントの処理でエラーが発生したら。

# コメント

## CommentEvent

コメント欄を監視する

> **place** `-> User|Studio|Project`

監視している場所

> **lastest_comment_dt** `-> datetime.datetime`

最後に確認されたコメントの時間

### event

> on_comment(comment)

**出力**
- **comment** (`Comment`) 投稿されたコメント

新しいコメントが見つかった時

# 通知(メッセージ)

## MessageEvent

通知の数を監視する

> **user** `-> User`

> **lastest_count** `-> int`

最新の通知の数

### event

> on_change(old,new)

**出力**
- **old** (`int`) 更新前の通知の数
- **new** (`int`) 更新後の通知の数

通知の数がかわったら

## SessionMessageEvent

> **session** `-> Session`

> **lastest_dt** `-> datetime.datetime`

### event

> on_activity(activity)

**出力**
- **activity** (`Activity`) 通知の内容