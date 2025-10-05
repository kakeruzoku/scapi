例外
====

.. contents::
    :depth: 3

例外の階層構造
--------------

* :class:`HTTPError <scapi.exceptions.HTTPError>`

  * :class:`SessionClosed <scapi.exceptions.SessionClosed>`
  * :class:`ProcessingError <scapi.exceptions.ProcessingError>`
  * :class:`ResponseError <scapi.exceptions.ResponseError>`

    * :class:`ClientError <scapi.exceptions.ClientError>` 

      * :class:`Unauthorized <scapi.exceptions.Unauthorized>`
      * :class:`Forbidden <scapi.exceptions.Forbidden>`

        * :class:`IPBanned <scapi.exceptions.IPBanned>`
        * :class:`AccountBlocked <scapi.exceptions.AccountBlocked>`
        * :class:`RegistrationRequested <scapi.exceptions.RegistrationRequested>`
        * :class:`ResetPasswordRequested <scapi.exceptions.ResetPasswordRequested>`
        * :class:`LoginFailure <scapi.exceptions.LoginFailure>`
        * :class:`CommentFailure <scapi.exceptions.CommentFailure>`

      * :class:`NotFound <scapi.exceptions.NotFound>`
      * :class:`TooManyRequests <scapi.exceptions.TooManyRequests>`

    * :class:`ServerError <scapi.exceptions.ServerError>`
    * :class:`InvalidData <scapi.exceptions.InvalidData>`

* :class:`CheckingFailed <scapi.exceptions.CheckingFailed>`

  * :class:`NoSession <scapi.exceptions.NoSession>`
  * :class:`NoDataError <scapi.exceptions.NoDataError>`

例外
----

.. autoclass:: scapi.exceptions.HTTPError

.. autoclass:: scapi.exceptions.SessionClosed

.. autoclass:: scapi.exceptions.ProcessingError

.. autoclass:: scapi.exceptions.ResponseError

.. autoclass:: scapi.exceptions.ClientError

.. autoclass:: scapi.exceptions.Unauthorized

.. autoclass:: scapi.exceptions.Forbidden

.. autoclass:: scapi.exceptions.IPBanned

.. autoclass:: scapi.exceptions.AccountBlocked

.. autoclass:: scapi.exceptions.RegistrationRequested

.. autoclass:: scapi.exceptions.ResetPasswordRequested

.. autoclass:: scapi.exceptions.LoginFailure

.. autoclass:: scapi.exceptions.CommentFailure

.. autoclass:: scapi.exceptions.NotFound

.. autoclass:: scapi.exceptions.TooManyRequests

.. autoclass:: scapi.exceptions.ServerError

.. autoclass:: scapi.exceptions.InvalidData

.. autoclass:: scapi.exceptions.CheckingFailed

.. autoclass:: scapi.exceptions.NoSession

.. autoclass:: scapi.exceptions.NoDataError