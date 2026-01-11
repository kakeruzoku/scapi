import asyncio
from typing import Any, Awaitable, Callable, TypeVar, ParamSpec, Coroutine, TYPE_CHECKING
from functools import wraps

P = ParamSpec("P")
R = TypeVar("R")


def async_wrapper(func: Callable[P, Coroutine[Any, Any, R]]) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Awaitable[R]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            return loop.create_task(func(*args, **kwargs))
        else:
            if TYPE_CHECKING:
                raise
            return asyncio.run(func(*args, **kwargs))
    return wrapper
