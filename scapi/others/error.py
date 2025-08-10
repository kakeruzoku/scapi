from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from . import requests

class HTTPerror(Exception):
    pass

class SessionClosed(HTTPerror):
    pass

class ProcessingError(HTTPerror):
    def __init__(self,exception:Exception):
        self.exception = exception

class ResponseError(HTTPerror):
    def __init__(self,response:"requests.Response"):
        self.response = response
        self.status_code = response.status_code

class ClientError(ResponseError):
    pass

class Unauthorized(ClientError):
    pass

class Forbidden(ClientError):
    pass

class IPBanned(Forbidden):
    def __init__(self,response:"requests.Response",ip:str|None):
        super().__init__(response)
        self.ip = ip

class AccountBlocked(Forbidden):
    #TODO 理由とか読み込む
    def __init__(self,response:"requests.Response"):
        super().__init__(response)

class NotFound(ClientError):
    pass

class TooManyRequests(ClientError):
    pass

class ServerError(ResponseError):
    pass

class CheckingFailed(Exception):
    pass

class NoSession(CheckingFailed):
    pass

class NoPermission(CheckingFailed):
    pass