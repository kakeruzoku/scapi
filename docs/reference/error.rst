例外
===================

例外の階層構造
-------------------------

* :class:`HTTPError <scapi.utils.error.HTTPError>`

  * :class:`SessionClosed <scapi.utils.error.SessionClosed>`
  * :class:`ProcessingError <scapi.utils.error.ProcessingError>`
  * :class:`ResponseError <scapi.utils.error.ResponseError>`

    * :class:`ClientError <scapi.utils.error.ClientError>` 

      * :class:`Unauthorized <scapi.utils.error.Unauthorized>`
      * :class:`Forbidden <scapi.utils.error.Forbidden>`

        * :class:`IPBanned <scapi.utils.error.IPBanned>`
        * :class:`AccountBlocked <scapi.utils.error.AccountBlocked>`
        * :class:`LoginFailure <scapi.utils.error.LoginFailure>`
        * :class:`CommentFailure <scapi.utils.error.CommentFailure>`

      * :class:`NotFound <scapi.utils.error.NotFound>`
      * :class:`TooManyRequests <scapi.utils.error.TooManyRequests>`

    * :class:`ServerError <scapi.utils.error.ServerError>`
    * :class:`InvalidData <scapi.utils.error.InvalidData>`

* :class:`CheckingFailed <scapi.utils.error.CheckingFailed>`

  * :class:`NoSession <scapi.utils.error.NoSession>`
  * :class:`NoPermission <scapi.utils.error.NoPermission>`
  * :class:`NoDataError <scapi.utils.error.NoDataError>`

例外
-------------------------

.. automodule:: scapi.utils.error