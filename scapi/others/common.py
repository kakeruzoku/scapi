import string
import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Coroutine, Generic, Literal, TypeVar, overload,AsyncContextManager
from . import error,client,config

BASE62_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase

def split(text:str,before:str,after:str) -> str|None:
    try:
        return text.split(before)[1].split(after)[0]
    except IndexError:
        return
    
def try_int(text:str) -> int | None:
    try:
        return int(text)
    except (ValueError, TypeError):
        return
    
def b62decode(text:str):
    text_len = len(text)
    return sum([BASE62_ALPHABET.index(text[i])*(62**(text_len-i-1)) for i in range(text_len)])

@overload
def dt_from_isoformat(timestamp:str|None) -> datetime.datetime|None:
    ...

@overload
def dt_from_isoformat(timestamp:str|None,allow_none:Literal[True]) -> datetime.datetime|None:
    ...

@overload
def dt_from_isoformat(timestamp:str,allow_none:Literal[False]) -> datetime.datetime:
    ...

def dt_from_isoformat(timestamp:str|None,allow_none:bool=True) -> None | datetime.datetime:
    if timestamp is None:
        if allow_none:
            return
        else:
            raise ValueError()
    return datetime.datetime.fromisoformat(timestamp).replace(tzinfo=datetime.timezone.utc)

@overload
def dt_from_timestamp(timestamp:float|None) -> datetime.datetime|None:
    ...

@overload
def dt_from_timestamp(timestamp:float|None,allow_none:Literal[True]) -> datetime.datetime|None:
    ...

@overload
def dt_from_timestamp(timestamp:float,allow_none:Literal[False]) -> datetime.datetime:
    ...

def dt_from_timestamp(timestamp:float|None,allow_none:bool=True) -> None | datetime.datetime:
    if timestamp is None:
        if allow_none:
            return
        else:
            raise ValueError()
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

async def api_iterative(
        _client:"client.HTTPClient",
        url:str,
        limit:int|None=None,
        offset:int|None=None,
        max_limit:int=40
    ) -> AsyncGenerator[Any, None]:
    limit = limit or max_limit
    offset = offset or 0
    for i in range(offset,offset+limit,max_limit):
        response = await _client.get(
            url,
            params={
                "limit":min(max_limit,limit-i),
                "offset":i,
            }
        )
        data = response.json()
        for i in data:
            yield i
        if not data:
            return

async def page_api_iterative(
        _client:"client.HTTPClient",
        url:str,
        start_page:int|None=None,
        end_page:int|None=None,
    ) -> AsyncGenerator[Any, None]:
    start_page = start_page or 1
    end_page = end_page or start_page
    for i in range(start_page,end_page+1):
        try:
            response = await _client.get(url,params={"page":i})
        except error.NotFound:
            return
        data = response.json()
        for i in data:
            yield i
        if not data:
            return

_T = TypeVar("_T")

def _bypass_checking(func:Callable[[_T], Any]) -> Callable[[_T], None]:
    def decorated(self:_T):
        if config.bypass_checking:
            return
        else:
            func(self)
    return decorated

class _AwaitableContextManager(Generic[_T]):
    def __init__(self, coro:Coroutine[Any, Any, AsyncContextManager[_T]]):
        self._coro = coro
        self._cm = None

    def __await__(self):
        return self._coro.__await__()

    async def __aenter__(self) -> _T:
        self._cm = await self._coro
        return await self._cm.__aenter__()

    async def __aexit__(self, exc_type, exc, tb):
        assert self._cm
        return await self._cm.__aexit__(exc_type, exc, tb)
    
empty_project_json = {
    'targets': [
        {
            'isStage': True,
            'name': 'Stage',
            'variables': {
                '`jEk@4|i[#Fk?(8x)AV.-my variable': [
                    'my variable',
                    0,
                ],
            },
            'lists': {},
            'broadcasts': {},
            'blocks': {},
            'comments': {},
            'currentCostume': 0,
            'costumes': [
                {
                    'name': '',
                    'bitmapResolution': 1,
                    'dataFormat': 'svg',
                    'assetId': '14e46ec3e2ba471c2adfe8f119052307',
                    'md5ext': '14e46ec3e2ba471c2adfe8f119052307.svg',
                    'rotationCenterX': 0,
                    'rotationCenterY': 0,
                },
            ],
            'sounds': [],
            'volume': 100,
            'layerOrder': 0,
            'tempo': 60,
            'videoTransparency': 50,
            'videoState': 'on',
            'textToSpeechLanguage': None,
        },
    ],
    'monitors': [],
    'extensions': [],
    'meta': {
        'semver': '3.0.0',
        'vm': '2.3.0',
        'agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    },
}