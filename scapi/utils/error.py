from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
from .types import (
    NoElementsPayload,
    LoginFailurePayload,
    CommentMuteStatusPayload,
    CommentFailurePayload,
    CommentFailureOldPayload,
    CommentPostPayload
)

if TYPE_CHECKING:
    from ..sites.base import _BaseSiteAPI
    from ..sites.session import Session
    from .client import Response

__all__ = [
    "HTTPError",
    "SessionClosed",
    "ProcessingError",
    "ResponseError",
    "ClientError",
    "Unauthorized",
    "Forbidden",
    "IPBanned",
    "AccountBlocked",
    "RegistrationRequested",
    "ResetPasswordRequested",
    "LoginFailure",
    "CommentFailure",
    "NotFound",
    "TooManyRequests",
    "ServerError",
    "InvalidData",
    "CheckingFailed",
    "NoSession",
    "NoDataError",
]

class HTTPError(Exception):
    pass

class SessionClosed(HTTPError):
    pass

class ProcessingError(HTTPError):
    def __init__(self,exception:Exception):
        self.exception = exception

class ResponseError(HTTPError):
    def __init__(self,response:"Response",message:Any=None):
        self.response = response
        self.status_code = response.status_code
        self.message = message

class ClientError(ResponseError):
    pass

class Unauthorized(ClientError):
    pass

class Forbidden(ClientError):
    pass

class IPBanned(Forbidden):
    def __init__(self,response:"Response",ip:str|None):
        super().__init__(response)
        self.ip = ip

class AccountBlocked(Forbidden):
    #TODO 理由とか読み込む
    def __init__(self,response:"Response"):
        super().__init__(response)

class RegistrationRequested(Forbidden):
    pass

class ResetPasswordRequested(Forbidden):
    pass

class LoginFailure(Forbidden):
    def __init__(self,response:"Response"):
        super().__init__(response)
        data:LoginFailurePayload = response.json()[0]
        self.username = data.get("username")
        self.num_tries = data.get("num_tries")
        self.request_capture = bool(data.get("redirect"))
        self.message = data.get("msg")

class CommentFailure(Forbidden):
    def __init__(
            self,
            response:"Response",
            session:"Session",
            content:str,
            type:str,
            status:CommentMuteStatusPayload|NoElementsPayload|None,
        ):
        super().__init__(response)
        self.type = type
        self.session = session
        if self.session and self.session.status and status is not None:
            self.session.status.mute_status = status
        self.mute_status = status
        self.timestamp:int = int(time.time())
        self.content = content

    @classmethod
    def _from_data(
            cls,
            response:"Response",
            session:"Session",
            content:str,
            data:CommentFailurePayload
        ):
        return cls(response,session,content,data.get("rejected"),data.get("status").get("mute_status"))
    
    @classmethod
    def _from_old_data(
            cls,
            response:"Response",
            session:"Session",
            content:str,
            data:CommentFailureOldPayload
        ):
        return cls(response,session,content,data.get("error"),data.get("mute_status"))
    
    async def feedback(self,message:str,language:str="en"):
        if self.session is None:
            raise NoSession(self.session)
        await self.session.client.post(
            "https://api.scratch.mit.edu/comments/feedback",
            json={
                "timestamp":self.timestamp,
                "feedback":message,
                "comment":self.content,
                "userId":self.session.user_id,
                "username":self.session.username,
                "language":language,
                "typeOfMessage":self.type
            }
        )

class NotFound(ClientError):
    pass

class TooManyRequests(ClientError):
    pass

class ServerError(ResponseError):
    pass

class InvalidData(ResponseError):
    pass

class CheckingFailed(Exception):
    def __init__(self,cls:"_BaseSiteAPI"):
        self.cls = cls

class NoSession(CheckingFailed):
    pass

class NoDataError(CheckingFailed):
    pass