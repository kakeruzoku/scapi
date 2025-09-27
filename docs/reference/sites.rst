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

.. autofunction:: scapi.get_remixtree

.. autoclass:: scapi.RemixTree


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

.. autoclass:: scapi.OcularStatus

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

.. |actor| replace:: :attr:`actor <scapi.Activity.actor>`
.. |place| replace:: :attr:`place <scapi.Activity.place>`
.. |target| replace:: :attr:`target <scapi.Activity.target>`
.. |activity_other| replace:: :attr:`other <scapi.Activity.other>`

.. autoclass:: scapi.ActivityType

.. autoclass:: scapi.ActivityAction

.. autoclass:: scapi.Activity

.. autoclass:: scapi.CloudActivity

フォーラム
----------

.. autofunction:: scapi.get_forum_categories

.. autofunction:: scapi.get_forum_category

.. autoclass:: scapi.ForumCategory

.. autofunction:: scapi.get_forum_topic

.. autoclass:: scapi.ForumTopic

.. autofunction:: scapi.get_forum_post

.. autoclass:: scapi.ForumPost

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