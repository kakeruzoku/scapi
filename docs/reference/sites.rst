サイトAPI
=========

.. contents::
    :depth: 3

ベースクラス
------------

.. autoclass:: scapi._BaseSiteAPI


アカウント
----------

.. autofunction:: scapi.login

.. autofunction:: scapi.session_login

.. autoclass:: scapi.Session

.. autoclass:: scapi.SessionStatus

プロジェクト
------------

.. autofunction:: scapi.get_project

.. autofunction:: scapi.Session.get_project
    :no-index:

.. autofunction:: scapi.explore_projects

.. autofunction:: scapi.search_projects

.. autoclass:: scapi.Project

.. autoclass:: scapi.ProjectFeatured

.. autoclass:: scapi.ProjectVisibility

スタジオ
--------

.. autofunction:: scapi.get_studio

.. autofunction:: scapi.Session.get_studio
    :no-index:

.. autofunction:: scapi.explore_studios

.. autofunction:: scapi.search_studios

.. autoclass:: scapi.Studio

.. autoclass:: scapi.StudioStatus

ユーザー
--------

.. autofunction:: scapi.get_user

.. autofunction:: scapi.Session.get_user
    :no-index:

.. autoclass:: scapi.User

コメント
--------

.. autoclass:: scapi.Comment

クラス
------

.. autofunction:: scapi.get_class

.. autofunction:: scapi.get_class_from_token

.. autoclass:: scapi.Classroom

アクティビティ
--------------

.. autoclass:: scapi.CloudActivity

フォーラム
----------

.. autofunction:: scapi.get_forum_categories

.. autoclass:: scapi.ForumCategory

.. autoclass:: scapi.ForumTopic

メインページ/統計
-----------------

.. autofunction:: scapi.get_news

.. autoclass:: scapi.News

.. autoclass:: scapi.CommunityFeaturedResponse

.. autofunction:: scapi.get_community_featured

その他
------

.. autoclass:: scapi.UsernameStatus

.. autofunction:: scapi.check_username

.. autoclass:: scapi.PasswordStatus

.. autofunction:: scapi.check_password

.. autoclass:: scapi.EmailStatus

.. autofunction:: scapi.check_email

.. autofunction:: scapi.translation

.. autofunction:: scapi.get_supported_translation_language

.. autofunction:: scapi.tts