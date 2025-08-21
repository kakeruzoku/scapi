from .types import (
    NoElementsPayload,
    LoginFailurePayload,
    CommentMuteStatusPayload,
    CommentFailurePayload,
    CommentFailureOldPayload
)
from . import client,common
from ..sites import base,session

class HTTPerror(Exception):
    pass

class SessionClosed(HTTPerror):
    pass

class ProcessingError(HTTPerror):
    def __init__(self,exception:Exception):
        self.exception = exception

class ResponseError(HTTPerror):
    def __init__(self,response:"client.Response"):
        self.response = response
        self.status_code = response.status_code

class ClientError(ResponseError):
    pass

class Unauthorized(ClientError):
    pass

class Forbidden(ClientError):
    pass

class IPBanned(Forbidden):
    def __init__(self,response:"client.Response",ip:str|None):
        super().__init__(response)
        self.ip = ip

class AccountBlocked(Forbidden):
    #TODO 理由とか読み込む
    def __init__(self,response:"client.Response"):
        super().__init__(response)

class LoginFailure(Forbidden):
    def __init__(self,response:"client.Response"):
        super().__init__(response)
        data:LoginFailurePayload = response.json()[0]
        self.username = data.get("username")
        self.num_tries = data.get("num_tries")
        self.request_capture = bool(data.get("redirect"))
        self.message = data.get("msg")

class CommentFailure(Forbidden):
    def __init__(
            self,
            response:"client.Response",
            session:"session.Session",
            type:str,
            status:CommentMuteStatusPayload|NoElementsPayload
        ):
        super().__init__(response)
        self.type = type
        self.session = session
        if self.session and self.session._status is not common.UNKNOWN:
            self.session._status.mute_status = status
        self.mute_status = status

    @classmethod
    def from_data(
        cls,
        response:"client.Response",
        session:"session.Session",
        data:CommentFailurePayload
    ):
        return cls(response,session,data.get("rejected"),data.get("status").get("mute_status"))
    
    @classmethod
    def from_old_data(
        cls,
        response:"client.Response",
        session:"session.Session",
        data:CommentFailureOldPayload
    ):
        return cls(response,session,data.get("error"),data.get("mute_status"))

class NotFound(ClientError):
    pass

class TooManyRequests(ClientError):
    pass

class ServerError(ResponseError):
    pass

class InvalidData(ResponseError):
    pass

class CheckingFailed(Exception):
    def __init__(self,cls:"base._BaseSiteAPI"):
        self.cls = cls

class NoSession(CheckingFailed):
    pass

class NoPermission(CheckingFailed):
    pass

class NoDataError(CheckingFailed):
    pass

del LoginFailurePayload,client