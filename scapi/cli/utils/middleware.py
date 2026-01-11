

from contextlib import contextmanager
from types import TracebackType
from typing import Iterable, Optional

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import typer
import scapi

from .common import console, show_error


class ProgressMiddleware:
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        )

    @contextmanager
    def add_task(self, text: str):
        task = self.progress.add_task(text, total=None)
        yield
        self.progress.stop_task(task)

    def __enter__(self):
        self.progress.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        self.progress.__exit__(exc_type, exc_val, exc_tb)


class ErrorMiddleware:
    def __init__(self, errors: dict[type[Exception], Iterable[str] | None]):
        self.errors = errors

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        if exc_val is None:
            return

        for k, v in self.errors.items():
            if isinstance(exc_val, k):
                if v is None:
                    break
                show_error(exc_val, v)

        return
