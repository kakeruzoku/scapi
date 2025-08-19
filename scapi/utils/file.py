from typing import IO, Any

from aiofiles.threadpool.binary import AsyncBufferedReader
import io
import aiofiles
from . import common

class File:
    def __init__(self,data:str|bytes|IO[bytes]|AsyncBufferedReader):
        self._fp:IO[bytes]|AsyncBufferedReader|None = None
        self._coro_fp = None
        if isinstance(data, (IO,AsyncBufferedReader)):
            self._fp = data
            self._owner = False
        elif isinstance(data, (bytes, bytearray, memoryview)):
            self._fp = io.BytesIO(data)
            self._owner = True
        elif isinstance(data, str):
            self._coro_fp = aiofiles.open(data, "rb")
            self._owner = True
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")
        
    async def _open(self):
        if self._fp is None:
            assert self._coro_fp
            self._fp = await self._coro_fp
        return self
    
    async def close(self):
        assert self._fp
        await common.maybe_coroutine(self._fp.close)
        
    @property
    def fp(self) -> IO[bytes] | AsyncBufferedReader:
        assert self._fp
        return self._fp
    
    def __await__(self):
        return self._open().__await__()

    async def __aenter__(self):
        return await self._open()
    
    async def __aexit__(self, exc_type, exc, tb):
        if self._owner:
            await self.close()

class _FileLike:
    def __init__(self,data):
        self.fp = data

def _file(data:Any) -> File|_FileLike:
    if isinstance(data,File):
        return data
    else:
        return _FileLike(data)
