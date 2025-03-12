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
  - ObjectNotFound get_objectでなかったとき
    - SessionNotFound Sessionがなかった時
    - UserNotFound ユーザーない
    - ProjectNotFound プロジェクトない
    - StudioNotFound スタジオない
    - CommentNotFound コメントない
    - ForumNotFound フォーラム関連
      - ForumTopicNotFound とぴっくない
      - ForumPostNotFound
    - ClassroomNotFound
- NoDataError Partial系のデータで、データが存在しないとき
"""

# http
class HTTPError(Exception):
    """
    通信でエラーが起きた時に出る
    """
class SessionClosed(Exception):
    """
    クライアントセッションが閉じてたときにでる
    """
class HTTPFetchError(HTTPError):
    """
    通信で失敗(レスポンスが返ってこなかったなど)したときに出る
    """
class ResponseError(HTTPError):
    """
    応答したが、エラーが起きた時に出る
    """
    def __init__(self, status_code:int, response:"Response"):
        self.status_code:int = status_code
        self.response:"Response" = response
class BadResponse(ResponseError):
    """
    {"code":"BadRequest","message":""}
    """
class BadRequest(ResponseError):
    """
    400番台が出た時に出す。
    """
class Unauthorized(BadRequest):
    """
    認証失敗(401/403)
    """
class HTTPNotFound(BadRequest):
    """
    404
    """
class TooManyRequests(BadRequest):
    """
    429
    """
class ServerError(ResponseError):
    """
    500が出た時
    """

class NoSession(Exception):
    """
    セッションが必要な操作をセッションなしで実行しようとした。
    """
class NoPermission(NoSession):
    """
    権限がない状態で実行しようとした。
    """

class LoginFailure(Exception):
    """
    ログイン失敗
    """


class CommentFailure(Exception):
    """
    コメント失敗
    """
    def __init__(self,type:str):
        self.type = type


class ObjectFetchError(Exception):
    """
    getしたけどエラー出た
    """
    def __init__(self,Class:"type[_BaseSiteAPI]",error):
        self.Class = Class
        self.error = error
class ObjectNotFound(ObjectFetchError):
    """
    getしたけどなかったてきなやつ
    """
class SessionNotFound(ObjectNotFound):
    """
    セッションでのログインに失敗
    """
class UserNotFound(ObjectNotFound):
    """
    ユーザーの取得に失敗
    """
class ProjectNotFound(ObjectNotFound):
    """
    プロジェクトの取得に失敗
    """
class RemixTreeNotFound(ObjectNotFound):
    """
    プロジェクトの取得に失敗
    """
class StudioNotFound(ObjectNotFound):
    """
    スタジオの取得に失敗
    """
class CommentNotFound(ObjectNotFound):
    """
    コメント取得失敗
    """
class ForumTopicNotFound(ObjectNotFound):
    """
    フォーラムトピック取得失敗
    """
class ForumPostNotFound(ObjectNotFound):
    """
    フォーラムトピック取得失敗
    """
class ClassroomNotFound(ObjectNotFound):
    """
    クラスない
    """
class AssetNotFound(ObjectNotFound):
    """
    アセットない
    """

class NoDataError(Exception):
    """
    データ不足
    """

class CloudError(Exception):
    """
    通信系
    """

class CloudConnectionFailed(CloudError):
    """接続失敗"""

class _cscc(CloudError):
    def __init__(self,code:int,reason:str):
        self.code:int = code
        self.reason:str = reason