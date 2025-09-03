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

.. autoclass:: scapi.Project

.. autoclass:: scapi.ProjectFeatured

.. autoclass:: scapi.ProjectVisibility

スタジオ
--------

.. autofunction:: scapi.get_studio

.. autofunction:: scapi.Session.get_studio
    :no-index:

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

アクティビティ
--------------

.. autoclass:: scapi.CloudActivity