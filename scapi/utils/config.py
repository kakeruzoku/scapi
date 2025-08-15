import aiohttp


bypass_checking:bool = False

def set_debug(mode:bool):
    global bypass_checking
    bypass_checking = mode

default_proxy:str|None=None
default_proxy_auth:aiohttp.BasicAuth|None=None

def set_default_proxy(url:str|None=None,auth:aiohttp.BasicAuth|None=None):
    global default_proxy,default_proxy_auth
    default_proxy = url
    default_proxy_auth = auth