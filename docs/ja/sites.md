# サイトAPI

ここではwebサイトのAPIを説明します。

# 目次
- [サイトAPI](#サイトapi)
- [目次](#目次)
- [共通事項](#共通事項)
- [ベースAPI](#ベースapi)
  - [ClientSession](#clientsession)
  - [Response](#response)
  - [\_BaseSiteAPI](#_basesiteapi)
- [アカウント](#アカウント)
  - [Session](#session)
  - [SessionStatus](#sessionstatus)
- [プロジェクト](#プロジェクト)
  - [Project](#project)
  - [RemixTree](#remixtree)
- [スタジオ](#スタジオ)
  - [Studio](#studio)
- [ユーザー](#ユーザー)
  - [User](#user)
  - [OcularStatus](#ocularstatus)
- [コメント](#コメント)
  - [Comment](#comment)
  - [~~UserComment~~](#usercomment)
- [フォーラム](#フォーラム)
  - [ForumCategoryType](#forumcategorytype)
  - [ForumTopic](#forumtopic)
  - [ForumPost](#forumpost)
  - [~~ForumStatus~~](#forumstatus)
  - [OcularReactions](#ocularreactions)
- [アクティビティ](#アクティビティ)
  - [Activity](#activity)
  - [ActivityType](#activitytype)
  - [CloudActivity](#cloudactivity)
- [クラス](#クラス)
  - [Classroom](#classroom)
- [アセット](#アセット)
  - [Backpack](#backpack)
- [トップページ](#トップページ)
  - [ScratchNews](#scratchnews)
- [その他](#その他)
- [例外](#例外)

# 共通事項

一部の引数は以下に記して省略します。

**入力**
- **limit** (`int`) 取得したい数
- **offset** (`int`) 初期位置
- **ClientSession** (`ClientSession`) 通信に使用するClientSession。
- **start_page** (`int`) 取得したい最初のページ数。
- **end_page** (`int`) 取得したい最後のページ数。

# ベースAPI

> scapi.**create_ClientSession(inp=None,Session=None)** `-> ClientSession`

**入力**
- **inp** (`ClientSession`) 
- **Session** (`Session`) 古いScratchのセッションを自動的に閉じるか

Scratch通信用のClientSessionを作成します。

## ClientSession
サイトと通信するためのクラス。(`asyncio.ClientSession`を継承)

> async with ... as ...

withから抜けるときに **close()** を実行します。

> property **header** `-> dict`

ヘッダーのコピー。

> property **cookie** `-> dict`

クッキーのコピー。

> property **proxy** `-> tuple[str|None,aiohttp.BasicAuth|None]`

設定されているプロキシ。

> **set_proxy(url=None,auth=None)**

**入力**
- **url** (`str|None`) プロキシURL
- **auth** (`aiohttp.BasicAuth|None`) 認証情報

プロキシを更新する

> **protect** `-> bool`

Scratch以外のサイトとの通信時にCookieやheaderの初期値を未ログイン状態にするか

通常`True`になりますが、カスタムで作成した場合は`False`になります。

**`1.4.0`で追加**

## Response
`ClientSession`でのレスポンスを表す

> **_response** `-> aasyncio.ClientResponse`

> **status_code** `-> int`

> **data** `-> bytes`

> property **text** `-> str`

bytesをstrに変換する

> **json()** `-> Any`

jsonを読み込む

> **headers** `-> dict`

レスポンスヘッダーのコピー

> **url** `-> str`

(リダイレクト済みの) URL

## _BaseSiteAPI
Scratchのなにかしらのオブジェクトを表す。このページにあるクラスほぼすべてが継承しています。

> async with ... as ...

withから抜けるときに **session_close()** を実行します。

> **check** `-> bool`

**`1.3.0`で追加**

Scapi内での権限チェックを行うか。`False`の場合、権限がないことがわかってもリクエストを行います。(他ユーザーのプロジェクトの`edit()`など)

> await **update**

データを更新します。クラスによっては何も起こらなかったり、一部データが更新されないことがあります。

> property **Session** `-> Session|None`

クラスに紐づけられているScratchのセッション。

> property **has_session** `-> bool`

Scratchのセッションを持っているか

> **link_session(session,if_close=False)** `-> Session|None`

**入力**
- **session** (`Session`) 新しいScratchのセッション。
- **if_close** (`bool`) 古いScratchのセッションを自動的に閉じるか

Scratchのセッションを変更する。古いScratchのセッションが返されます。

> property **ClientSession** `-> ClientSession`

クラスに紐づけられているClientSession。

> property **session_closed** `-> bool`

ClientSessionが閉じられているか。

> await **session_close()**

クラスに紐づけられているClientSessionを(開いていたら)閉じます。通常、あるオブジェクトから新たにオブジェクトが作成された場合は、ClientSessionを引き継ぎます。**そのため、`get_****`等で作成したオブジェクトは閉じる必要があります。**

# アカウント

> await scapi.**login(username,password,*,ClientSession=None)** `-> Session`

**入力**
- **username** (`str`) ログインしたいユーザー名
- **password** (`str`) ログインしたいパスワード

Scratchにログインします。ログイン後は`Session`ごとに新しいClientSessionが作成されます。

> await scapi.**session_login(session_id)** `-> Session`

**入力**
- **session_id** (`str`) 使用したいアカウントのセッションID

Scratchのアカウントに接続します。

> await scapi.**send_password_reset_email(clientsession,username="",email="")** `-> bool|None`

**入力**
- **username** (`str`) メールを送信したいアカウント名。
- **email** (`str`) メールを送信したいメールアドレス。

パスワードリセットメールを送信します。ユーザー名かメールアドレスのどちらかが必要です。

**戻り値** メールが送信されたか。不明な場合は`None`を返します。

## Session
Scratchのセッションを表すクラス。

> **status** `-> SessionStatus`

アカウントの情報を見る

> **session_id** `-> str`

> **xtoken** `-> str|None`

> **is_email_verified** `-> bool`

> **email** `-> str`

> **scratcher** `-> bool`

> **mute_status** `-> dict`

> **username** `-> str`

> **banned** `-> bool`

> **session_decode()** `-> dict`

sessionIDをデコードします。IPアドレスやxtoken、ユーザーIDなどの情報が含まれています。

> await **logout()**

ログアウトして、ClientSessionを閉じます。

> await **change_password(old_password,new_password)**

**入力**
- **old_password** (`str`) 現在使用しているパスワード
- **new_password** (`str`) 新しいパスワード

**`1.5.0`で追加**

> await **change_country(country)**

**入力**
- **country** (`str`) 変更先の地域

**`1.5.0`で追加**

> await **change_email(password,email)**

**入力**
- **password** (`str`) 現在使用しているパスワード
- **email** (`str`) 変更先のメールアドレス

**`1.5.0`で追加**

> await **delete_account(password,delete_project)**

**入力**
- **password** (`str`) 現在使用しているパスワード
- **delete_project** (`bool`) プロジェクトを非共有にするか

**`1.5.0`で追加**

> await **me()** `-> User`

ログインしているアカウントのユーザークラスを取得します。

> **create_Partial_myself()** `-> User`

ログインしているアカウントの部分的なユーザークラスを作成します。

**`1.5.0`で変更** アカウントのユーザークラスに対してキャッシュを作成するようになりました。

Userにある情報:username,id,_join_date,join_date

> await **my_classroom()** `-> Classroom|None`

生徒アカウントの場合、所属しているクラスのクラスを取得します。

> await **create_project(self,title="Untitled",project_json=None,remix_id=None)** `-> Project`

**入力**
- **title** (`str`) 使用したいタイトル
- **project_json** (`dict|None`) 送信したいプロジェクトデータ。Noneで初期プロジェクトです。
- **remix_id** (`int|None`) リミックスしたい場合、そのプロジェクトID。

> await **create_studio()**

スタジオを作成する

> await **create_class(title,about_class="",wiwo="")**

**入力**
- **title** (`str`)
- **about_class** (`str`)
- **wiwo** (`str`)

教師アカウントの場合、クラスを作成する。

**`2.0.0`で追加**

> async for **message(limit=40, offset=0)** `-> Activity`

メッセージを取得します。

> **message_event(interval=30)** `-> SessionMessageEvent`

**入力**
- **interval** (`int`) 更新する時間

> await **message_count()** `-> int`

**`1.4.0`で追加**

> await **clear_message()**

**`1.4.0`で追加**

> await **check_scratcher_invite()** `-> dict|None`

Scratcherへの招待情報を見る。

**`2.0.0`で追加**

> await **become_scratcher()**

Scratcher招待がある場合、Scratcherになる。

**`2.0.0`で追加**

> async for **following_feed(limit=40, offset=0)** `-> Activity`

最新の情報欄を取得する。

> async for **following_loves(limit=40, offset=0)** `-> Project`

フォロワーが好きなプロジェクトを取得する。

> async for **backpack(limit=40, offset=0)** `-> Backpack`

バックパックを取得する。

> async for **viewed_projects(limit=40, offset=0)** `-> Project`

閲覧したプロジェクトの履歴を取得する。

> async for **get_mystuff_projects(start_page=1,end_page=1,type="all",sorted="",descending=True)**

**入力**
- **type** (`str`) 取得するデータの種類。`all` `shared` `notshared` `trashed`が使えます。
- **sort** (`str`) ソートする内容。 `view_count` `love_count` `remixers_count` `title`が使えます。
- **descending** (`bool`) ソートの向き

**`1.5.0`で追加**

**`2.0.0`で更新** 名前が`get_mystuff_project`から変更されました。(非推奨ですが、`get_mystuff_project`も利用可能です。)

> async for **get_mystuff_studios(start_page=1,end_page=1,type="all",sorted="",descending=True)**

**入力**
- **type** (`str`) 取得するデータの種類。`all` `owned` `curated`が使えます。
- **sort** (`str`) ソートする内容。 `projecters_count` `title`が使えます。
- **descending** (`bool`) ソートの向き

**`1.5.0`で追加**

**`2.0.0`で更新** 名前が`get_mystuff_studio`から変更されました。(非推奨ですが、`get_mystuff_studio`も利用可能です。)

> async for **get_mystuff_classes(start_page=1,end_page=1,type="all",sorted="",descending=True)**

**入力**
- **type** (`str`) 取得するデータの種類。`all` `closed`が使えます。
- **sort** (`str`) ソートする内容。 `studnet_count` `title`が使えます。
- **descending** (`bool`) ソートの向き

**`2.0.0`で追加**

> await **get_mystuff_class(id)**

**入力**
- **id** (`int`) 取得したいクラスのID

**`2.0.0`で追加**

> await **get_mystuff_students(start_page=1,end_page=1)**

**`2.0.0`で追加**


> await **check_educator_password(password)**

**入力**
- **password** (`str`) 判定したいパスワード

教師アカウントの場合、アカウントのパスワードかどうか確認する。

> await **upload_asset(data,file_ext="")**

**入力**
- **data** (`bytes|str`) 画像のバイナリデータか画像のファイルパス
- **ile_ext** (`str`) (bytesで入れた場合、)ファイルの拡張子

ファイルをアップロードする

**`1.5.0`で追加**

> await **empty_trash(password)**

**入力**
- **password** アカウントのパスワード

**`1.5.0`で追加**

> **get_cloud(project_id:)** `-> ScratchCloud`

**`1.3.0`で追加**

**入力**
- **project_id** (`int`) 取得したいプロジェクトのID

> await **get_project(project_id)** `-> Project`

**入力**
- **project_id** (`int`) 取得したいプロジェクトのID

> await **get_user(username)** `-> User`

**入力**
- **username** (`str`) 取得したいユーザー名

> await **get_studio(studio_id)** `-> Studio`

**入力**
- **studio_id** (`int`) 取得したいスタジオのID

> await **get_forumtopic(topic_id)** `-> ForumTopic`

**入力**
- **topic_id** (`int`) 取得したいトピックのID

> await **get_forumpost(post_id)** `-> ForumPost`

**入力**
- **post_id** (`int`) 取得したい投稿のID

> await **get_classroom(classroom_id)** `-> Classroom`

**入力**
- **post_id** (`int`) 取得したい投稿のID

> async for **explore_projects(query="*", mode="trending", language="en" ,limit=40, offset=0)** `-> Project`

**入力**
- **query** (`str`) ?
- **mode** (`str`) 取得するタイプ
- **language** (`str`) 言語

> async for **search_projects(query, mode="trending", language="en" ,limit=40, offset=0)** `-> Project`

**入力**
- **query** (`str`) 検索したい文字
- **mode** (`str`) 取得するタイプ
- **language** (`str`) 言語

> async for **explore_studios(query="*", mode="trending", language="en" ,limit=40, offset=0)** `-> Studio`

**入力**
- **query** (`str`) ?
- **mode** (`str`) 取得するタイプ
- **language** (`str`) 言語

> async for **search_studios(query, mode="trending", language="en" ,limit=40, offset=0)** `-> Studio`

**入力**
- **query** (`str`) 検索したい文字
- **mode** (`str`) 取得するタイプ
- **language** (`str`) 言語

## SessionStatus

アカウントの状態を表します。いろいろ不明です。

> **confirm_email_banner** `-> bool`

> **everything_is_totally_normal** `-> bool`

> **gallery_comments_enabled** `-> bool`

> **has_outstanding_email_confirmation** `-> bool`

> **must_complete_registration** `-> bool`

> **must_reset_password** `-> bool`

> **project_comments_enabled** `-> bool`

> **show_welcome** `-> bool`

> **unsupported_browser_banner** `-> bool`

> **userprofile_comments_enabled** `-> bool`

> **with_parent_email** `-> bool `

親のメアドを登録しているか

> **admin** `-> bool `

> **educator** `-> bool `

教師垢てきな

> **educator_invitee** `-> bool`

承認前の教師アカウント

> **invited_scratcher** `-> bool `

> **mute_status** `-> dict`

コメントのミュートのステータス?

> **new_scratcher** `-> bool `

> **scratcher** `-> bool `

> **social** `-> bool`

> **student** `-> bool `

> **banned** `-> bool `

> **birthMonth** `-> int `

> **birthYear** `-> int `

> **classroomId** `-> int|None `

> **dateJoined** `-> str `

入った日時 datetime版は SessionStatus.joined_dt

> **email** `-> str `

> **gender** `-> str `

> **id** `-> int `

> **should_vpn** `-> bool `

VPNがいるか ST垢でTrueになるらしい

> **thumbnailUrl** `-> str `

> **token** `-> str `

X token

> **username** `-> str `

> **joined_dt** `-> datetime.datetime `

入った日時

# プロジェクト

> await scapi.**get_project(project_id,*,ClientSession=None)** `-> Project`

**入力**
- **project_id** (`int`) 取得したいプロジェクトのID

> await Session.**get_project(project_id)** `-> Project`

**入力**
- **project_id** (`int`) 取得したいプロジェクトのID

> scapi.**create_Partial_Project(project_id,author=None,*,ClientSession=None,session=None)**

**入力**
- **project_id** (`int`) 作成したいプロジェクトのID
- **author** (`User|None`) プロジェクトの作成者
- **Session** (`Session`) セッション

仮のオブジェクトを作成します。

> async for scapi.**explore_projects(query="*", mode="trending", language="en" ,limit=40, offset=0,ClientSession:ClientSession=None)** `-> Project`

**入力**
- **query** (`str`) ?
- **mode** (`str`) 取得するタイプ
- **language** (`str`) 言語

傾向を取得します。

> async for scapi.**search_projects(query, mode="trending", language="en" ,limit=40, offset=0,ClientSession:ClientSession=None)** `-> Project`

**入力**
- **query** (`str`) 検索したい文字
- **mode** (`str`) 取得するタイプ
- **language** (`str`) 言語

プロジェクトを検索します。

> await **get_remixtree(project_id,ClientSession=None,session=None)** `-> RemixTree`

**入力**
- **project_id** (`int`) プロジェクトID
- **Session** (`Session`) 関連付けたいアカウントのセッション

リミックスツリーを取得します。

## Project

Scratchのプロジェクトページを表すクラス。

> == =!

同じプロジェクトを指しているか

> \> < => =< 

プロジェクトIDで比較

> **id** `-> int`

> **project_token** `-> str|None`

プロジェクトjsonを取得するためのトークン

> **author** `-> User`

プロジェクトの作者

> **title** `-> str`

> **instructions** `-> str`

プロジェクトの使い方欄

> **notes** `-> str`

プロジェクトのメモとクレジット

> **loves** `-> int`

> **favorites** `-> int`

> **remix_count** `-> int`

> **views** `-> int`

> **_created** `-> str`

> **created** `-> datetime.datetime`

> **_shared** `-> str`

> **shared** `-> datetime.datetime`

> **_modified** `-> str`

> **modified** `-> datetime.datetime`

> **comments_allowed** `-> bool`

> **remix_parent** `-> int`

> **remix_root** `-> int`

> **comment_count** `-> int|None`

「私の作品」からでのみ取得できる情報。

**`1.5.0`で追加**

> property **_is_owner** `-> bool`

プロジェクトの作者か

> property **thumbnail_url** `-> str`

サムネイルURL

> property **url** `-> str`

> async for **remixes(limit=40, offset=0)** `-> Project`

子プロジェクトを取得します。(一部情報だけが欲しいならremixtreeから取得したほうが早いです。)

> await **create_remix(title=None)** `-> Project`

リミックスします。プロジェクトが公開されていなくても実行できます。

**入力**
- **title** (`str|None`) プロジェクトのタイトル。 Noneで自動的に設定されます。

> await **load_json(update=True)** `-> dict`

**入力**
- **update** (`bool`) tokenを最新の状態に更新するか。

> await **download(save_path,filename=None,log=False)** `-> str`

**入力**
- **save_path** (`str`) 保存したいディレクトリ
- **filename** (`str|None`) sb3ファイルの名前。(.sb3 がない場合は挿入されます。) Noneなら自動生成されます。
- **log** (`bool`) ログをprintするか

プロジェクトを(画像、音声も含めて)ダウンロードして、sb3ファイルに圧縮します。ファイル操作が行われるため、ディレクトリ内のファイルの名前に気をつけてください。保存先のパスが返されます。

> await **love(love=True)** `-> bool`

**入力**
- **love** (`bool`) 変更先の状態。

プロジェクトの好きステータスを変更します。ステータスが変更されたかが返されます。

> await **favorite(favorite=True)** `-> bool`

**入力**
- **favorite** (`bool`) 変更先の状態。

プロジェクトのお気に入りステータスを変更します。ステータスが変更されたかが返されます。

> await **view()** `-> bool`

プロジェクトの閲覧回数を1増やします。実際に値が増やされたかが返ります。

> await **edit(comment_allowed=None,title=None,instructions=None,notes=None)**

**入力**
- **comment_allowed** (`bool|None`) コメントを許可するか
- **title** (`str|None`) プロジェクト名
- **instructions** (`str|None`) プロジェクトの使い方欄
- **notes** (`str|None`) プロジェクトのメモとクレジット欄

プロジェクトページを更新します。`None`は変更せずにそのままになります。

> await **old_edit(title=None,share=None,trash=None)**

**入力**
- **title** (`str|None`) プロジェクト名
- **share** (`bool|None`) 共有するか
- **trash** (`bool|None`) ゴミ箱に入れるかどうか

2.0時代のAPIを使用してプロジェクト情報を更新します。`None`は変更せずにそのままになります。

**`1.5.0`で追加**

> await **set_thumbnail(thumbnail)**

**入力**
- **thumbnail** (`bytes|str`) 画像のバイナリデータか画像のファイルパス

プロジェクトのサムネイルを更新します。

> await **set_json(data)**

**入力**
- **data** (`dict|str`) アップロードしたいプロジェクトのjsonデータ

プロジェクトデータをアップロードします。

> async for **studios(limit=40, offset=0)** `-> Studio`

プロジェクトが入っているスタジオのリスト。

> await **get_comment_by_id(id,is_old=None)** `-> Comment`

**入力**
- **id** (`int`) 取得したいコメントのID
- **is_old** (`bool|None`) 古いAPIを使うかどうか。`None`で自動的に選択されます。

**`2.0.0`で更新** 古いAPIも利用できるようになりました。

> async for **get_comments(limit=40, offset=0, start_page=1, end_page=1, is_old=None)** `-> Comment`

**入力**
- **is_old** (`bool|None`) 古いAPIを使うかどうか。`None`で自動的に選択されます。

**`2.0.0`で更新** 古いAPIも利用できるようになりました。

> await **post_comment(content,parent=None,commentee=None,is_old=None)** `-> Comment`

**入力**
- **content** (`str`) 投稿したいコメントの文章
- **parent** (`int|Comment|None`) 返信する場合は、返信先のコメントID
- **commentee** (`int|User|None`) メンションしたいユーザーのID
- **is_old** (`bool|None`) 古いAPIを使うかどうか。`None`で自動的に選択されます。

コメントを送信します。送信されたコメントオブジェクトを返します。

> **comment_event(interval=30)** `-> CommentEvent`

**入力**
- **interval** (`int`) 更新する時間

> await **share(share=True)**

**入力**
- **share** (`bool`) 変更先の状態。

プロジェクトの共有の状態を変更します。

> await **visibility()** `-> dict`

プロジェクトのステータスを取得します。(プロジェクトの作者のみ可能)

> await **report(category,message)**

**入力**
- **category** (`int`) 報告の種類
- **message** (`str`) メッセージ本文

報告の種類は以下を確認してください。
```
0 他のプロジェクトの完全なコピー
1 クレジットせずに画像や音楽を流用している
2 過度に暴力的だったり恐怖心をあおる
3 不適切な表現が含まれる
4 不適切な音楽が使用されている
5 個人的な連絡先情報が公開されている
6 その他
7 ???
8 不適切な画像
9 このプロジェクトはミスリードしているか、コミュニティーをだましています
10 これは顔写真を公開するプロジェクトだったり、だれかの写真を見せようとしています
11 このプロジェクトをリミックスすることが禁止されています
12 このプロジェクトの作者の安全が心配です
13 その他
14 怖い画像
15 ジャンプスケア
16 暴力的な出来事
17 現実的な武器の使用
18 他のScratcherに対する脅迫やいじめ
19 Scratcherやグループに対して意地悪だったり失礼である
```

**`2.0.0`で追加**

> await **get_remixtree()** `-> RemixTree`

リミックスツリーを取得します。

> **get_cloud** `-> ScratchCloud`

**`1.3.0`で追加**

Scratchクラウドを表すクラスを返します。(詳細は /cloud まで)

> async for **get_cloud_logs(limit=100, offset=0)** `-> CloudActivity`

**`1.3.0`で追加**

> **cloud_log_event(interval=1)** `-> CloudLogEvent`

**`1.3.0`で追加**

## RemixTree
リミックスツリーの中のプロジェクトを表すクラス。update()による更新は現在できません。プロジェクトによっては大きくメモリを消費する可能性があります。

> **id** `-> int`

プロジェクトID

> **is_root** `-> bool`

一番下のプロジェクトか

> **project** `-> Project`

プロジェクトクラスを返す

Projectにある情報: author,title,remix_parent,loves,modified,shared,favorites
Project.author(User)にある情報: Username

> **moderation_status** `-> str`

STによるプロジェクトの評価を返す

> **ctime** `-> datetime`

よくわからん

> property **parent** `-> RemixTree|None`

親プロジェクトを返します

> property **children** `-> list[RemixTree]`

子プロジェクトのリストを返します

> property **root** `-> RemixTree`

親プロジェクトを返します

> property **all_remixtree** `-> list[RemixTree]`

このプロジェクトが含まれているリミックスツリーのプロジェクト全てを返します。


# スタジオ

> await scapi.**get_studio(studio_id,*,ClientSession=None)** `-> Studio`

**入力**
- **studio_id** (`int`) 取得したいスタジオのID

> await Session.**get_studio(studio_id)** `-> Studio`

**入力**
- **studio_id** (`int`) 取得したいスタジオのID

> scapi.**create_Partial_Studio(studio_id,*,ClientSession=None,session=None)**

**入力**
- **studio_id** (`int`) 作成したいスタジオのID
- **Session** (`Session`) セッション

仮のオブジェクトを作成します。

> async for scapi.**explore_studios(query="*", mode="trending", language="en" ,limit=40, offset=0,ClientSession:ClientSession=None)** `-> Studio`

**入力**
- **query** (`str`) ?
- **mode** (`str`) 取得するタイプ
- **language** (`str`) 言語

傾向を取得します。

> async for scapi.**search_studios(query, mode="trending", language="en" ,limit=40, offset=0,ClientSession:ClientSession=None)** `-> Studio`

**入力**
- **query** (`str`) 検索したい文字
- **mode** (`str`) 取得するタイプ
- **language** (`str`) 言語

プロジェクトを検索します。

## Studio

スタジオを表すクラス。「ギャラリー(gallery)」はスタジオを指します。

> == =!

同じスタジオを指しているか

> \> < => =< 

スタジオIDで比較

> **id** `-> int`

> **title** `-> str`

> **description** `-> str`

> **author_id** `-> int`

> **open_to_all** `-> bool`

キュレーターでなくてもプロジェクトを追加できるか

> **comments_allowed** `-> bool`

> **created** `-> datetime.datetime`

> **modified** `-> datetime.datetime`

最終更新時間

> **follower_count** `-> int`

> **manager_count** `-> int`

> **project_count** `-> int`

100まで

> **comment_count** `-> int`

100まで

> **curator_count** `-> int|None`

キュレーターの数? 「私の作品」からでのみ取得できます。

**`1.5.0`で追加**

> property **image_url** `-> str`

> property **url** `-> str`

> property **_is_owner** `-> bool`

> await **get_comment_by_id(id,is_old=None)** `-> Comment`

**入力**
- **id** (`int`) 取得したいコメントのID
- **is_old** (`bool|None`) 古いAPIを使うかどうか。`None`で自動的に選択されます。

**`2.0.0`で更新** 古いAPIも利用できるようになりました。

> async for **get_comments(limit=40, offset=0, start_page=1, end_page=1, is_old=None)** `-> Comment`

**入力**
- **is_old** (`bool|None`) 古いAPIを使うかどうか。`None`で自動的に選択されます。

**`2.0.0`で更新** 古いAPIも利用できるようになりました。

> await **post_comment(content,parent=None,commentee=None,is_old=None)** `-> Comment`

**入力**
- **content** (`str`) 投稿したいコメントの文章
- **parent** (`int|Comment|None`) 返信する場合は、返信先のコメントID
- **commentee** (`int|User|None`) メンションしたいユーザーのID
- **is_old** (`bool|None`) 古いAPIを使うかどうか。`None`で自動的に選択されます。

コメントを送信します。送信されたコメントオブジェクトを返します。

> **comment_event(interval=30)** `-> CommentEvent`

**入力**
- **interval** (`int`) 更新する時間

> await **follow(follow)**

**入力**
- **follow** (`bool`) 変更先の状態。

> await **set_thumbnail(thumbnail,filename="image.png")**

**入力**
- **thumbnail** (`bytes|str`) 画像のバイナリデータか画像のファイルパス
- **filename** (`str`) (bytesで入れた場合、)拡張子を含んだファイル名

> await **edit(title=None,description=None,trash=None)**

**入力**
- **title** (`str|None`) タイトル
- **description** (`str|None`) 説明
- **trash** (`bool|None`) 削除するか

スタジオを更新します。`None`は変更せずにそのままになります。

**`2.0.0`で更新** スタジオを削除するか選択できるようになりました。

> await **open_adding_project(is_open=True)**

**入力**
- **is_open** (`bool`) 変更先の状態。

> await **open_comment(is_open=True,is_update=True)**

**入力**
- **is_open** (`bool`) 変更先の状態。
- **is_update** (`bool`) データを更新して、確実に切り替えるか

コメント欄の開け閉めを行います。APIが`toggle-comments`なため、`comments_allowed`の状態に応じてリクエストを送信します。

> await **invite(username)**

**入力**
- **username** (`str|User`) 招待したいユーザー

> await **accept_invite()**

招待を受け取る

> await **promote(username)**

**入力**
- **username** (`str|User`) 昇格したいユーザー

> await **transfer_ownership(username,password)**

**入力**
- **username** (`str|User`) 譲渡したいユーザー
- **password** (`str`) あなたのアカウントのパスワード

> await **remove_user(username)**

**入力**
- **username** (`str|User`) 削除したいユーザー

> await **leave()**

キュレーターやマネージャーから自分を削除する

> await **add_project(project_id)**

**入力**
- **project_id** (`int|Project`) 追加したいプロジェクトのID

> await **remove_project(project_id)**

**入力**
- **project_id** (`int|Project`) 削除したいプロジェクトのID

> async for **projects(limit=40, offset=0)** `-> Project`

> async for **curators(limit=40, offset=0)** `-> User`

> await **host()** `-> User`

スタジオ所有者を取得。

> async for **managers(limit=40, offset=0)** `-> User`

> async for **activity(limit=40, datelimit=0)** `-> Activity`

**入力**
- **datelimit** (`datetime.datetime|None`) offset的な役割。指定した時間より前のアクティビティを取得する。Noneで最新の情報を取得。

> await **classroom()** `-> Classroom|None`

クラススタジオの場合、クラスを取得する。

**`2.x.x`で追加**

> await **roles()** `-> dict[str,bool]`

あなたのスタジオでの役割を確認する。

> await **report(type)**

**入力**
- **type** (`str`) `title`,`description`,`thumbnail`から選択できます。

**`2.0.0`で追加**

# ユーザー


> await scapi.**get_user(username,*,ClientSession=None)** `-> User`

**入力**
- **username** (`str`) 取得したいユーザーのユーザー名

> await Session.**get_user(username)** `-> User`

**入力**
- **username** (`str`) 取得したいユーザーのユーザー名

> scapi.**create_Partial_User(username,user_id=None,*,ClientSession=None,session=None)**

**入力**
- **username** (`str`) 作成したいユーザーのユーザー名
- **user_id** (`int`) ユーザーのユーザーID(あれば)
- **Session** (`Session`) セッション

## User

ユーザーを表すクラス。

> == =!

同じユーザーを指しているか

> \> < => =< 

ユーザーIDで比較

> **id** `-> int`

> **username** `-> username`

> **join_date** `-> datetime.datetime`

> **about_me** `-> str`

> **wiwo** `-> str`

> **country** `-> str`

> **scratchteam** `-> bool`

ここから下は一部方法でのみ取得できます。(**`2.0.0`で追加**)

> **educator_can_unban** `-> bool|None`

> **force_password_reset** `-> bool|None`

> **banned** `-> bool|None`

> **email** `-> str|None`

> **forum_status** `-> str|None`

> **forum_post_count** `-> int|None`

(ここまで)

> property **icon_url** `-> str`

> property **url** `-> str`

**`2.0.0`で追加**

> await **load_website(reload:bool=False)**

**入力**
- **reload** (`bool`) 情報がすでにあった場合、リクエストを行うか

> await **exist(use_cache=True)** `-> bool`

**入力**
- **user_cache** (`bool`) キャッシュがある場合、キャッシュを使うか

ユーザーページが存在するか。存在しない場合は下の3つの関数はNoneです。

> await **is_new_scratcher(use_cache=True)** `-> bool|None`

**入力**
- **user_cache** (`bool`) キャッシュがある場合、キャッシュを使うか

> await **classroom_id(use_cache=True)** `-> int|None`

**入力**
- **user_cache** (`bool`) キャッシュがある場合、キャッシュを使うか


> await **classroom(use_cache=True)** `-> Classroom|None`

**入力**
- **user_cache** (`bool`) キャッシュがある場合、キャッシュを使うか

> await **message_count()** `-> int`

> await **message_event(interval=30)** `-> MessageEvent`

**入力**
- **interval** (`int`) 更新する時間

> await **featured_data()** `-> dict`

Project(key:`object`)に含まれる情報:id,title

注目のプロジェクトを取得します。(key:label,id,title,object)

> await **follower_count()** `-> int`

> await **followers(limit=40, offset=0)** `-> User`

> await **following_count()** `-> int`

> await **following(limit=40, offset=0)** `-> User`

> await **is_followed(username)**

**入力**
- **username** (`str|User`) 確認したいユーザー

入力したユーザーにフォローされているか

> await **is_following(username)**

**入力**
- **username** (`str|User`) 確認したいユーザー

入力したユーザー名をフォローしているか

> await **project_count()** `-> int`

> await **projects(limit=40, offset=0)** `-> Project`

> await **favorite_count()** `-> int`

> await **favorites(limit=40, offset=0)** `-> Project`

> await **love_count()** `-> int`

> await **loves(start_page=1, end_page=1)** `-> Project`

> async for **activity(limit=1000)** `-> Activity`

1年前までのユーザーのアクティビティを取得します。

> await **get_comment_by_id(id,is_old=None)** `-> Comment`

**入力**
- **id** (`int`) 取得したいコメントのID
- **is_old** (`bool|None`) 古いAPIを使うかどうか。`None`で自動的に選択されます。

**`2.0.0`で更新** 古いAPIも利用できるようになりました。

> async for **get_comments(limit=40, offset=0, start_page=1, end_page=1, is_old=None)** `-> Comment`

**入力**
- **is_old** (`bool|None`) 古いAPIを使うかどうか。`None`で自動的に選択されます。

**`2.0.0`で更新** 古いAPIも利用できるようになりました。

> await **post_comment(content,parent=None,commentee=None,is_old=None)** `-> Comment`

**入力**
- **content** (`str`) 投稿したいコメントの文章
- **parent** (`int|Comment|None`) 返信する場合は、返信先のコメントID
- **commentee** (`int|User|None`) メンションしたいユーザーのID
- **is_old** (`bool|None`) 古いAPIを使うかどうか。`None`で自動的に選択されます。

コメントを送信します。送信されたコメントオブジェクトを返します。

> **comment_event(interval=30)** `-> CommentEvent`

**入力**
- **interval** (`int`) 更新する時間

> await **toggle_comment()**

コメントの開閉を切り替えます。APIにコメントが開いているか確認するものがないため、toggleのみの実装になります。

> await **edit(about_me=None,wiwo=None,featured_project_id=None,featured_label=None)**

**入力**
- **about_me** (`str|None`) 「私について」欄
- **wiwo** (`str|None`)「私が取り組んでいること」欄
- **featured_project_id** (`int|None`) 注目のプロジェクトのプロジェクトID
- **featured_label** (`str|None`) 注目のプロジェクトのラベル

> await **set_icon(icon,filename="icon.png")**

**入力**
- **icon** (`bytes|str`) 画像のバイナリデータか画像のファイルパス
- **filename** (`str`) (bytesで入れた場合、)拡張子を含んだファイル名

> await **follow(follow)**

**入力**
- **follow** (`bool`) 変更先の状態。

> await **get_ocular_status** `-> OcularStatus`

**`1.4.0`で追加**

> await **reset_student_password(password=None)**

**入力**
- **password** (`str|None`) 新しいパスワード。`None`の場合、教師アカウント名に設定され、次回ログイン時に入力させる画面を表示させます。

生徒の場合、パスワードをリセットまたは変更する。

> await **report(type)**

**入力**
- **type** (`str`) `title`,`description`,`thumbnail` `working_on`から選択できます。

**`2.0.0`で追加**

## OcularStatus

Ocularでのステータスを表す。

アカウント情報がないユーザーは、データが`None`になります。

> **id** `-> int|None`

> **username** `-> str`

> **status** `-> str|None`

> **color** `-> int|None`

> **updated** `-> datetime.datetime|None`

# コメント

> **create_Partial_Comment(comment_id,place,content=None,author=None,ClientSession=None,session=None)** `-> Comment`

**入力**
- **comment_id** (`int`)
- **place** (`User|Studio|Project`) コメントの場所
- **content** (`str|None`) 本文
- **author** (`User|None`) 投稿主

## Comment

通常のコメントを表します。

ユーザーページの場合、古いAPIしか利用できないことに注意してください。

**`2.0.0`で更新** `UserComment`と結合しました。

> **id** `-> int`

> **place** `-> Project|Studio|User`

> **type** `-> Literal["Project","Studio","User"]`

> **parent_id** `-> int|None`

> **commentee_id** `-> int|None`

> **content** `-> str`

> **send** `-> datetime.datetime`

**`2.0.0`で変更** `sent_dt`から`sent`に変更されました。(`sent_dt`は非推奨)

> **author** `-> User`

> **reply_count** `-> int`

> await **update(is_old:bool|None)**

**入力**
- **is_old** (`bool|None`) 古いAPIを使うか。`None`の場合、できるだけ新しいAPIを使用しようとします。

**`2.0.0`で更新** 古いAPIも利用できるようになりました

> await **get_parent_comment(use_cache=True)** `-> Comment|None`

**入力**
- **user_cache** (`bool`) キャッシュがある場合、キャッシュを使うか

> async for **get_replies(limit=40, offset=0)** `-> Comment`

新APIが利用できない場合はキャッシュからアクセスしようとします。(キャッシュは2.0APIでのみ保持されます。)

> await **reply(content,commentee_id=None)**

**入力**
- **content** (`str`) 投稿したいコメントの文章
- **commentee_id** (`int|User|None`) メンションしたいユーザー(ID) (Noneでコメントを投稿した人)

> await **delete(is_old:bool|None)** `-> bool`

**入力**
- **is_old** (`bool|None`) 古いAPIを使うか

**`2.0.0`で更新**

> await **report()** `-> bool`

**入力**
- **is_old** (`bool|None`) 古いAPIを使うか

**`2.0.0`で更新** 古いAPIも利用できるようになりました

## ~~UserComment~~

**`2.0.0`で削除** `Comment`にまとめられました。

# フォーラム

APIがないのでbeautifulsoupでの実装が多めです。Scratchの仕様変更により、利用不可能になることがあります。

> await scapi.**get_topic(topic_id,*,ClientSession=None)** `-> ForumTopic`

**入力**
- **topic_id** (`int`) 取得したいトピックのID

> await scapi.**get_post(post_id,*,ClientSession=None)** `-> ForumPost`

**入力**
- **post_id** (`int`) 取得したい投稿のID

> await Session.**get_topic(topic_id)** `-> ForumTopic`

**入力**
- **topic_id** (`int`) 取得したいトピックのID

> await Session.**get_post(post_id)** `-> ForumPost`

**入力**
- **post_id** (`int`) 取得したい投稿のID

> scapi.**create_Partial_ForumTopic(topic_id,*,ClientSession=None,session=None)**

**入力**
- **topic_id** (`int`) 作成したいトピックのID
- **Session** (`Session`) セッション

> scapi.**create_Partial_ForumTopic(post_id,topic=None,*,ClientSession=None,session=None)**

**入力**
- **post_id** (`int`) 作成したい投稿のID
- **topic** (`ForumTopic|None`) 投稿されたトピック 
- **Session** (`Session`) セッション

仮のオブジェクトを作成します。

> scapi.**get_topic_list(category,start_page=1,end_page=1,ClientSession=None)**

**入力**
- **category** (`ForumCategoryType`) 読み込みたいカテゴリー

カテゴリーのトピックを取得します。

## ForumCategoryType

フォーラムのカテゴリーを表します。(`_BaseSiteAPI`を継承していません！)

> classmethod **value_of(target_value)** `-> ForumCategoryType`

**入力**
- **target_value** (`int`) カテゴリーのID

IDからカテゴリーを作成します。不明なIDは`ForumCategoryType.unknown`(ID=0)が返されます。

## ForumTopic

トピックを表します。一部データ(is_stickyなど)は一部の方法でしか取得できません。

> **id** `-> int`

> **title** `-> str`

> **category** `-> category`

> **last_page** `-> int`

> **is_sticky** `-> bool|None`

> **is_closed** `-> bool|None`

> **view_count** `-> int|None`

> **last_update** `-> str|None`

> async for **self,start_page=1,end_page=1** `-> ForumPost`

フォーラムの投稿を取得します。

## ForumPost

フォーラムの投稿を表します。

> **id** `-> int`

> **topic** `-> ForumTopic`

> **author** `-> User`

Userにある情報:username,id

> **page** `-> int`

> **number** `-> int`

> ~~**author_status**~~

**`2.0.0`で削除**

> **content** `-> str`

> **time** `-> str`

> property **url** `-> str`

## ~~ForumStatus~~

**`2.0.0`で削除** `User`にまとめられました。

## OcularReactions

フォーラムの投稿のリアクションを見る

**`1.4.0`で追加**

> **id** `-> int`

> **thumbs_up** `-> list[str]`

リアクションをしたユーザーのリスト

> **thumbs_down** `-> list[str]`

> **smile** `-> list[str]`

> **tada** `-> list[str]`

> **confused** `-> list[str]`

> **heart** `-> list[str]`

> **rocket** `-> list[str]`

> **eyes** `-> list[str]`

# アクティビティ

> async for Session.**message(limit=40, offset=0)** `-> Activity`

メッセージを取得します。

> async for Session.**following_feed(limit=40, offset=0)** `-> Activity`

最新の情報欄を取得する。

> async for User.**activity(limit=1000)** `-> Activity`

1年前までのユーザーのアクティビティを取得します。

> async for Studio.**activity(limit=40, datelimit=0)** `-> Activity`

**入力**
- **datelimit** (`datetime.datetime|None`) offset的な役割。指定した時間より前のアクティビティを取得する。Noneで最新の情報を取得。

スタジオでのアクティビティを取得します。

## Activity

何かしらの活動を表します。

現在、メッセージ/フィード/スタジオの活動/ユーザーの活動/クラスの活動 に対応しています。

> **id** `-> int`

> **type** `-> ActivityType`

> **actor** `-> User|None`

実行した人

> **target** `-> Comment|Studio|Project|User|None`

活動を行った先

> **place** `-> Studio|Project|User|None`

活動が行われた場所

> **datetime** `-> datetime.datetime`

## ActivityType

アクティビティの種類を表すクラス。(`_BaseSiteAPI`を継承していません！)

## CloudActivity

クラウド変数の変更を示すクラス

> **method** `-> str`

> **variable** `-> str`

> **value** `-> str`

> **username** `-> str|None`

> **project_id** `-> int`

> **datetime** `-> datetime`

**`1.3.0`で追加**

> **cloud** `-> _BaseCloud|CloudServerConnection|None`

> await **get_user()** `-> User`

> await **get_project()** `-> Project`

# クラス

> await scapi.**get_classroom(class_id,*,ClientSession=None)** `-> Classroom`

**入力**
- **class_id** (`int`) 取得したいクラスのID

> await scapi.**get_classroom_by_token(class_token,*,ClientSession=None)** `-> Classroom`

**入力**
- **class_token** (`int`) 取得したいクラスの招待トークン

> await Session.**get_classroom(class_id)** `-> Classroom`

**入力**
- **class_id** (`int`) 取得したいクラスのID

> await Session.**get_classroom_by_token(class_token)** `-> Classroom`

**入力**
- **class_token** (`int`) 取得したいクラスの招待トークン

> scapi.**create_Partial_Classroom(class_id,class_token=None,*,ClientSession=None,session=None)** `-> Classroom`

**入力**
- **class_id** (`int`) 作成したいクラスのID
- **class_token** (`str|None`) クラスの招待トークン
- **Session** (`Session`) セッション

仮のオブジェクトを作成します。

## Classroom

クラスを表します。

> **id** `-> int`

> **classtoken** `-> str|None`

> **title** `-> str`

> **created** `-> datetime.datetime`

> **educator** `-> User`

> **about_class** `-> str`

**`2.0.0`で追加**

> **wiwo** `-> str`

**`2.0.0`で追加**

> **_studio_count** `-> int|None`

**`2.0.0`で追加**

> **_student_count** `-> int|None`

**`2.0.0`で追加**

> **commenter_count** `-> int|None`

**`2.0.0`で追加**

> await **studio_count()** `-> int`

> async for **studios(start_page=1, end_page=1, is_website=None)** `-> Studio`

**入力**
- **is_website** (`bool|None`) `False`は教師アカウントでのみ使用できます。`None`では、自動的に判断されます。

**`2.0.0`で追加** 教師アカウント用APIを追加

> await **student_count()** `-> int`

> async for **students(start_page=1, end_page=1,is_website=None)** `-> User`

**入力**
- **is_website** (`bool|None`) `False`は教師アカウントでのみ使用できます。`None`では、自動的に判断されます。

**`2.0.0`で追加** 教師アカウント用APIを追加

> await **edit(title,about_class,wiwo)**

**入力**
- **title** (`str|None`)
- **about_class** (`str|None`)
- **wiwo** (`str|None`)

**`2.0.0`で追加**

> await **set_icon(icon,filename="icon.png")**

**入力**
- **icon** (`bytes|str`) 画像のバイナリデータか画像のファイルパス
- **filename** (`str`) (bytesで入れた場合、)拡張子を含んだファイル名

**`2.0.0`で追加**

> async for **get_privete_activity(start_page=1, end_page=1, type="all", sort="", descending=True)** `-> Activity`

**入力**
- **type** (`str`) 取得するデータの種類。`all` ユーザー名 が使えます。
- **sort** (`str`) ソートする内容。 `username` が使えます。
- **descending** (`bool`) ソートの向き

**`2.0.0`で追加**

> await **create_class_studio(title,description)**

**入力**
- **title** (`str`)
- **description** (`str`)

**`2.0.0`で追加**

> await **create_student_account(username,password,birth_day,gender,country)**

**入力**
- **username** (`str`) アカウントのユーザー名
- **password** (`str`) パスワード
- **birth_day** (`datetime.date`) 誕生日(年と月が使用されます。)
- **gender** (`str`) 性別
- **country** (`str`) 国

Scratchの生徒アカウントを作成します。

# アセット

> async for **backpack(limit=40, offset=0)** `-> Backpack`

バックパックを取得する。

## Backpack

バックパックを表します。

> **id** `-> str`

> **type** `-> Backpacktype`

> **name** `-> str`

> property **download_url** `-> str`

> property **thumbnail_url** `-> str`

> await **download(path)**

**入力**
- **path** (`str`) ダウンロード先のパス

> await **delete()**


# トップページ

> async for **get_scratchnews(limit=40, offset=0, clientsession=None)** `-> ScratchNews`

ニュースを取得する。

> await **community_featured(clientsession=None,session=None)** `-> dict[str,list[Project|Studio]|Studio]`

コミュニティが好きなものを取得します。レスポンスの詳細は型ヒントを確認してください。

## ScratchNews

Scratchのニュースを示す。

> **id** `-> int`

> **timestamp** `-> datetime.datetime`

> **url** `-> str`

> **image_url** `-> str`

> **title** `-> str`

> **content** `-> str`

# その他

> scapi.**check_username(username,clientsession)** `-> bool`

**入力**
- **username** (`str`) 確認したいユーザー名

ユーザー名が利用できるか確認します。

> scapi.**check_password(password,clientsession)** `-> bool`

**入力**
- **password** (`str`) 確認したいパスワード

パスワードが利用できるか確認します。

> scapi.**total_site_stats(clientsession)** `-> dict[str,int|float]`

全体の統計を取得します。

> scapi.**monthly_site_traffic(clientsession)** `-> dict[str,int|float]`

月の統計を取得します。

> scapi.**monthly_activity(clientsession)** `-> dict[str,dict[str,list[tuple[int,int]]]|float]`

月ごとの統計(グラフ)を取得します。レスポンスの詳細は型ヒントを確認してください。

> scapi.**translation(language,text,clientsession)** `-> str`

**入力**
- **language** (`str`) 言語コード(`ja`,`en`など)
- **text** (`str`) 翻訳したい文

Google翻訳を使います。

> scapi.**tts(language,text,type,clientsession)** `-> bytes`

**入力**
- **language** (`str`) 言語コード(`ja`,`en`など)
- **text** (`str`) しゃべりたい内容
- **type** (`Literal["male","female"]`) 喋る人

> scapi.**is_allowed_username(username)** `-> str`

**入力**
- **username** (`str`)

ユーザー名がScratchで有効か確認する。

# 例外
`scapi.exceptions`からアクセスできます。

- `HTTPError` `ClientSession`内でのエラー。基本的に下の例外が出てくる
  - `SessionClosed` セッションを既に閉じている場合に、リクエストをしようとした
  - `HTTPFetchError` リクエストの受信→処理 の間にエラーが起こった
  - `ResponseError` レスポンスがエラーである \*
    - `IPBanned` IPBAN画面にリダイレクトした
    - `AccountBrocked` アカウントブロック画面にリダイレクトした
    - `BadRequest` 4xx
      - `Unauthorized` 401 or 403
      - `TooManyRequests` 429
      - `HTTPNotFound` 404
    - `ServerError` 5xx
    - `BadResponse` なにかに失敗した

- `NoSession` アカウントにログインしていない状態でログインしが必要なリクエストを**しようとした**
  - `NoPermission` 権限がない状態で権限が必要なリクエストを**しようとした**

- `CommentFailure` コメントがブロックされた

- `LoginFailure` ログインに失敗した

- `ObjectFetchError` オブジェクトを取得しようとして、なんらかのエラーが発生した。
  - `ObjectNotFound` オブジェクトが存在しない

- `NoDataError` リクエストに必要な情報を持っていない