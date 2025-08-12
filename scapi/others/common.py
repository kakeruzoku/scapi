import string
import datetime
from typing import TYPE_CHECKING, Any, AsyncGenerator, Literal, overload
from . import error

if TYPE_CHECKING:
    from . import client

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
        limit:int|None,
        offset:int=0,
        max_limit:int=40
    ) -> AsyncGenerator[Any, None]:
    limit = limit or max_limit
    for i in range(offset,offset+limit,max_limit):
        response = await _client.get(
            url,
            params={
                "limit":min(max_limit,limit-i),
                "offset":offset,
            }
        )
        for i in response.json():
            yield i

async def page_api_iterative(
        _client:client.HTTPClient,
        url:str,
        start_page:int=1,
        end_page:int|None=None,
    ) -> AsyncGenerator[Any, None]:
    end_page = end_page or start_page
    for i in range(start_page,end_page+1):
        try:
            response = await _client.get(url,params={"page":i})
        except error.NotFound:
            return
        for i in response.json():
            yield i