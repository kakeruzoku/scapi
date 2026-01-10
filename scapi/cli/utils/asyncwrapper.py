import asyncio
from typing import Any, Callable, TypeVar, ParamSpec, Coroutine
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")


def async_wrapper(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return asyncio.run(func(*args, **kwargs))
    return wrapper
