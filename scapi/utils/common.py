from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from enum import Enum
import string
import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Coroutine, Generic, Literal, ParamSpec, Protocol, Self, Sequence, TypeVar, overload,AsyncContextManager
import inspect
from functools import wraps

import bs4

from .error import NotFound
from .config import _config
if TYPE_CHECKING:
    from .client import HTTPClient
    from ..sites.session import Session

__version__ = "3.1.4"

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_T = TypeVar("_T")

BASE62_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase

Tag = bs4.Tag|Any

class _Special(Enum):
    UNKNOWN = "UNKNOWN"

    def __repr__(self):
        return "<UNKNOWN>"
    
    def __eq__(self, value):
        return False
    
    def __bool__(self) -> Literal[False]:
        return False

UNKNOWN = _Special.UNKNOWN
UNKNOWN.__doc__ = "「不明」を表す定数。"
UNKNOWN_TYPE = Literal[_Special.UNKNOWN]
UNKNOWN_TYPE.__doc__ = "UNKNOWNを表す型ヒント"
MAYBE_UNKNOWN = _T|UNKNOWN_TYPE

del _Special

async def do_nothing(*args,**kwargs):
    pass

class UnknownDict(dict[_KT, _VT]):
    @overload  # default が None の場合
    def get(self, key: _KT, default: UNKNOWN_TYPE = UNKNOWN, /) -> _VT | UNKNOWN_TYPE: ...
    @overload  # default が値と同じ型の場合
    def get(self, key: _KT, default: _VT, /) -> _VT: ...
    @overload  # default が任意型の場合
    def get(self, key: _KT, default: _T, /) -> _VT | _T: ...

    def get(self, key: _KT, default: Any = UNKNOWN, /) -> Any: # type: ignore
        return super().get(key, default)

@overload
def split(text:str,before:str,after:str,forced:Literal[True]) -> str:
    ...

@overload
def split(text:str,before:str,after:str,forced:Literal[False]=False) -> str|None:
    ...

def split(text:str,before:str,after:str,forced:bool=False) -> str|None:
    try:
        return text.split(before)[1].split(after)[0]
    except IndexError:
        if forced:
            raise ValueError() from None
        
async def get_any_count(client:HTTPClient,url:str,before:str,after:str=")") -> int:
    response = await client.get(url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    _head:Tag = soup.find("div",{"class":"box-head"})
    return int(split(str(_head.find("h2")),before,after,True))

def try_int(text:str) -> int | None:
    try:
        return int(text)
    except (ValueError, TypeError):
        return
    
def b62decode(text:str):
    text_len = len(text)
    return sum([BASE62_ALPHABET.index(text[i])*(62**(text_len-i-1)) for i in range(text_len)])

@overload
def dt_from_isoformat(timestamp:str|_T) -> datetime.datetime|_T:
    ...

@overload
def dt_from_isoformat(timestamp:str|_T,allow_unknown:Literal[True]) -> datetime.datetime|_T:
    ...

@overload
def dt_from_isoformat(timestamp:str|Any,allow_unknown:Literal[False]) -> datetime.datetime:
    ...

def dt_from_isoformat(timestamp:str|_T,allow_unknown:bool=True) -> datetime.datetime|_T:
    if not isinstance(timestamp,str):
        if allow_unknown:
            return timestamp
        else:
            raise ValueError()
    return datetime.datetime.fromisoformat(timestamp).replace(tzinfo=datetime.timezone.utc)

@overload
def dt_from_timestamp(timestamp:float|_T) -> datetime.datetime|_T:
    ...

@overload
def dt_from_timestamp(timestamp:float|_T,allow_unknown:Literal[True]) -> datetime.datetime|_T:
    ...

@overload
def dt_from_timestamp(timestamp:float|Any,allow_unknown:Literal[False]) -> datetime.datetime:
    ...

def dt_from_timestamp(timestamp:float|_T,allow_unknown:bool=True) -> datetime.datetime|_T:
    if not isinstance(timestamp,(float,int)):
        if allow_unknown:
            return timestamp
        else:
            raise ValueError()
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

def dt_to_str(dt:datetime.datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    dt = dt.astimezone(datetime.timezone.utc)
    return f"{dt.strftime('%Y-%m-%dT%H:%M:%S')}.{dt.microsecond//1000:03d}Z"

async def api_iterative(
        _client:"HTTPClient",
        url:str,
        limit:int|None=None,
        offset:int|None=None,
        max_limit:int=40,
        params:dict[str,str|int|float]|None=None
    ) -> AsyncGenerator[Any, None]:
    params = params or {}
    limit = limit or max_limit
    offset = offset or 0
    for i in range(offset,offset+limit,max_limit):
        response = await _client.get(
            url,
            params={
                "limit":min(max_limit,offset+limit-i),
                "offset":i,
            }|params
        )
        data = response.json()
        for i in data:
            yield i
        if not data:
            return

async def page_api_iterative(
        _client:"HTTPClient",
        url:str,
        start_page:int|None=None,
        end_page:int|None=None,
        params:dict[str,str|int|float]|None=None
    ) -> AsyncGenerator[Any, None]:
    params = params or {}
    start_page = start_page or 1
    end_page = end_page or start_page
    for i in range(start_page,end_page+1):
        try:
            response = await _client.get(url,params={"page":i}|params)
        except NotFound:
            return
        data = response.json()
        for i in data:
            yield i
        if not data:
            return
        
async def page_html_iterative(
        _client:"HTTPClient",
        url:str,
        start_page:int|None=None,
        end_page:int|None=None,
        params:dict[str,str|int|float]|None=None,
        *,
        outside_class:str|None="media-grid",
        list_class:str,
        list_name:str|None="li"
    ) -> AsyncGenerator[Tag,None]:
    params = params or {}
    start_page = start_page or 1
    end_page = end_page or start_page
    for i in range(start_page,end_page+1):
        try:
            response = await _client.get(url,params={"page":i}|params)
        except NotFound:
            return
        data:Tag = bs4.BeautifulSoup(response.text, "html.parser")
        if outside_class is not None:
            data = data.find("div",{"class":outside_class})
        
        objs:Sequence[Tag] = data.find_all(list_name,{"class":list_class}) # pyright: ignore[reportArgumentType]
        for obj in objs:
            yield obj
        

class APIIterativeFunc(Protocol):
    def __call__(self, limit:int|None=None, offset:int|None=None,*args: Any, **kwds: Any) -> AsyncGenerator[Any,None]:
        ...

class PageAPIIterativeFunc(Protocol):
    def __call__(self, start_page:int|None=None, end_oage:int|None=None,*args: Any, **kwds: Any) -> AsyncGenerator[Any,None]:
        ...

def _count_func(
    func:APIIterativeFunc|PageAPIIterativeFunc,
    is_page:bool,
    *args,
    **kwargs,
) -> Callable[[int,int], Coroutine[Any, Any, int]]:
    if is_page:
        async def _func(c:int,max_limit:int) -> int:
            return len([i async for i in func(c,None,*args,**kwargs)])
    else:
        async def _func(c:int,max_limit:int) -> int:
            return len([i async for i in func(max_limit,(c-1)*max_limit,*args,**kwargs)])
    return _func

@overload
async def count_api_iterative(
    func:APIIterativeFunc,
    is_page:Literal[False]=False,
    max_limit:int=40,
    *args,
    **kwargs,
) -> int:
    ...
    
@overload
async def count_api_iterative(
    func:PageAPIIterativeFunc,
    is_page:Literal[True],
    max_limit:int=40,
    *args,
    **kwargs,
) -> int:
    ...

async def count_api_iterative(
    func:APIIterativeFunc|PageAPIIterativeFunc,
    is_page:bool=False,
    max_limit:int=40,
    *args,
    **kwargs,
) -> int:
    """
    データ一覧を取得する関数から、そのデータの長さを特定する。

    2種類の関数が使用できます。
    - タイプ A: 1番目に ``limit``, 2番目に ``offset`` を取る関数
    - タイプ B: 1番目に ``start_page``, 2番目に ``end_page`` を取る関数

    Args:
        func (Callable): タイプ A または タイプ B の関数 
        is_page (bool, optional): タイプ B の場合 ``True`` にしてください。
        max_limit (int, optional): その関数が1回で取得できる最大の数。基本的に ``40`` です。 **正しい値でない場合、結果が正しく返されません。**

    Returns:
        int: そのデータの値
    """
    _func = _count_func(func,is_page,*args,**kwargs)

    # 最大値を決定する
    c = 1
    while True:
        objs_len = await _func(c,max_limit)
        print(c,objs_len)
        if objs_len == 0:
            low = c//2
            high = c
            break
        elif objs_len < max_limit:
            return (c-1)*max_limit+objs_len
        c *= 2

    if low == 0:
        return 0
    
    # 二分探索
    while True:
        if high-low <= 1:
            return low*max_limit
        mid = (low+high)//2
        objs_len =  await _func(mid,max_limit)
        print(mid,objs_len)
        if objs_len == 0:
            high = mid
        elif objs_len < max_limit:
            return ((mid-1)*max_limit)+objs_len
        else:
            low = mid

def get_client_and_session(client_or_session:"HTTPClient|Session|None") -> tuple["HTTPClient","Session|None"]:
    from .client import HTTPClient
    if client_or_session is None:
        return HTTPClient(), None
    if isinstance(client_or_session,HTTPClient):
        return client_or_session, None
    else:
        return client_or_session.client, client_or_session


_T = TypeVar("_T")
_P = ParamSpec('_P')

@asynccontextmanager
async def temporary_httpclient(client_or_session:"HTTPClient|Session|None"):
    need_close = client_or_session is None
    client,_ = get_client_and_session(client_or_session)
    try:
        yield client
    except:
        if need_close:
            await client.close()
        raise

async def wait_all_event(*events:asyncio.Event):
    while True:
        if all(event.is_set() for event in events):
            return
        await asyncio.gather(*[event.wait() for event in events])

def _bypass_checking(func:Callable[[_T], Any]) -> Callable[[_T], None]:
    @wraps(func)
    def decorated(self:_T):
        """
        このチェックはデバックモードにすることで回避できます。
        """
        if _config.bypass_checking:
            return
        else:
            func(self)
    return decorated

class _SelfContextManager(AsyncContextManager,Protocol):
    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, exc_type, exc, tb) -> bool|None: ...

_AT = TypeVar("_AT", bound="_SelfContextManager")

class _AwaitableContextManager(Generic[_AT]):
    """
    Coroutineからasync withとawaitどちらにも対応できるようにするクラス。

    obj = await coro または async with coro as obj: のようにして使用できます。

    .. note::
        特別な理由がない限りは async with で使用すべきです。
        awaitのみで使用する場合は、最後に実行すべき関数 (.client_close())などを確認してください。

    """
    def __init__(self, coro:Coroutine[Any,Any,_AT]):
        self._coro = coro
        self._cm = None

    def __await__(self):
        return self._coro.__await__()

    async def __aenter__(self) -> _AT:
        self._cm = await self._coro
        return await self._cm.__aenter__()

    async def __aexit__(self, exc_type, exc, tb):
        assert self._cm
        return await self._cm.__aexit__(exc_type, exc, tb)
    
async def maybe_coroutine(func:Callable[_P,Coroutine[Any,Any,_T]|_T],*args:_P.args,**kwargs:_P.kwargs) -> _T:
    maybe_coro = func(*args,**kwargs)
    if inspect.isawaitable(maybe_coro):
        return await maybe_coro
    else:
        return maybe_coro
    
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