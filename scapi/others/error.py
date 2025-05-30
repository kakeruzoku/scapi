from enum import Enum
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .common import Response
    from ..sites.base import _BaseSiteAPI

"""
階層表記
- HTTPError 通信時でのエラー
  - SessionClosed セッションが閉じてた
  - HTTPFetchError レスポンスが帰って来なかった
  - ResponseError 応答でエラーが起こった
    - BadResponse {"code":"BadRequest","message":""} など失敗した。
    - BadRequest 4xx
      - Unauthorized 401 or 403
      - HTTPNotFound 404
      - TooManyRequests 429
    - ServerError 5xx
- NoSession セッションなし
  - NoPermission 権限なし
- LoginFailure ログイン失敗
- ObjectFetchError get_objectでエラー
  - ObjectNotFound なにかを取得しようとしてなかったとき
- NoDataError Partial系のデータで、データが存在しないとき
"""

# http
class HTTPError(Exception):
    "`ClientSession`内でのエラー 基本的に下の例外が出てくる"
class SessionClosed(HTTPError):
    "セッションを既に閉じている場合に、リクエストをしようとした"
class HTTPFetchError(HTTPError):
    "リクエストの受信→処理 の間にエラーが起こった"
class ResponseError(HTTPError):
    "レスポンスの内容が失敗だった"
    def __init__(self, response:"Response"):
        self.status_code:int = response.status_code
        self.response:"Response" = response
class BadResponse(ResponseError):
    "本体の内容が失敗を示している"
class BadRequest(ResponseError):
    "4xx"
class Unauthorized(BadRequest):
    "401/403"
class HTTPNotFound(BadRequest):
    "404"
class TooManyRequests(BadRequest):
    "429"
class ServerError(ResponseError):
    "5xx"
class AccountBrocked(ResponseError):
    "アカウントブロック画面にリダイレクトした"
class IPBanned(ResponseError):
    "IPBAN画面にリダイレクトした"

class NoSession(Exception):
    "セッションが必要な操作をセッションなしで実行しようとした。"
class NoPermission(NoSession):
    "権限がない状態で実行しようとした。"

class LoginFailure(Exception):
    "ログイン失敗"

class CommentFailure(Exception):
    def __init__(self,type:str):
        self.type = type


class ObjectFetchError(Exception):
    "エラー"
    def __init__(self,Class:"type[_BaseSiteAPI]",error=None):
        self.Class = Class
        self.error = error
class ObjectNotFound(ObjectFetchError):
    "404"

class NoDataError(Exception):
    "データ不足"

class CloudError(Exception):
    "通信系"

class CloudConnectionFailed(CloudError):
    "接続失敗"

class _cscc(CloudError):
    def __init__(self,code:int,reason:str):
        self.code:int = code
        self.reason:str = reason