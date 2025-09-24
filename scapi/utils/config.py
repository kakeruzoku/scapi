import aiohttp

class Config:
    def __init__(self) -> None:
        self.default_proxy:str|None = None
        self.default_proxy_auth:aiohttp.BasicAuth|None = None
        self.bypass_checking:bool = False

_config = Config()

def set_debug(mode:bool):
    _config.bypass_checking = mode

def set_default_proxy(url:str|None=None,auth:aiohttp.BasicAuth|None=None):
    """
    デフォルトのプロキシを設定する。

    Args:
        url (str | None, optional): 使用するプロキシのURL。
        auth (aiohttp.BasicAuth | None, optional): プロキシの認証情報。
    """
    _config.default_proxy = url
    _config.default_proxy_auth = auth