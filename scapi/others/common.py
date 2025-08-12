import string
import datetime
from typing import Literal, overload

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