from __future__ import annotations

from contextlib import asynccontextmanager
from typing import IO, Any, AsyncGenerator, Generator

from aiofiles.threadpool.binary import AsyncBufferedReader
import io
import aiofiles
from .common import maybe_coroutine

class File:
    """
    ファイルを表すクラス。

    このクラスは、ファイルの非同期操作を簡単に扱えるように設計されています。

    オブジェクト生成後の使用方法:

    - await する場合:
        オブジェクトを ``await`` するときは、使用後に必ず ``await file.close()`` を呼び出してファイルを閉じる必要があります。

    - async with を使用する場合:
        ``async with`` ブロックを抜ける際に、ファイルは自動的に閉じられます。

    - なにもしない場合:
        オブジェクトを何もせず生成した場合は、必ず対応しているscapiの関数に1度だけ入力してください。
        関数に渡すと、自動的にファイルが開かれ、処理終了後に閉じられます。
        直接生成して放置することはできません。

        これは ``file=scapi.File()`` のような操作を想定しています
    """
    def __init__(self,data:str|bytes|IO[bytes]|AsyncBufferedReader):
        """
        Args:
            data (str | bytes | IO[bytes] | AsyncBufferedReader): データ本体またはファイルパスまたはファイルオブジェクト

        Raises:
            TypeError: 処理できないデータ形式
        """
        self._fp:IO[bytes]|AsyncBufferedReader|None = None
        self._coro_fp = None
        self._opened = False
        self._need_close = False
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
        self._opened = True
        return self
    
    async def read(self) -> bytes:
        return await maybe_coroutine(self.fp.read)
    
    async def close(self):
        assert self._fp
        await maybe_coroutine(self._fp.close)
        
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

@asynccontextmanager
async def _file(data:Any) -> AsyncGenerator[File | _FileLike,None]:
    if isinstance(data,File):
        if data._opened:
            yield data
        else:
            async with data:
                yield data
    else:
        yield _FileLike(data)

@asynccontextmanager
async def _read_file(data:File|bytes) -> AsyncGenerator[bytes]:
    if isinstance(data,File):
        if data._opened:
            yield await data.read()
        else:
            async with data:
                yield await data.read()
    else:
        yield data
