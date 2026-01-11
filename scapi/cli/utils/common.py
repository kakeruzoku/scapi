from pathlib import Path
from typing import Iterable, NoReturn
import click
from rich.console import Console

from rich.panel import Panel
import typer

APP_NAME = "scapi"

console = Console()

app_dir = Path(typer.get_app_dir(APP_NAME)).resolve()


def create_app_folder():
    app_dir.mkdir(parents=True, exist_ok=True)


def show_error(error: Exception, text: Iterable[str]) -> NoReturn:
    if isinstance(text, str):
        text = (text,)
    console.print(Panel("\n".join(
        text), title=f"Error: {error.__class__.__name__}", border_style="red b"))
    raise typer.Abort()


def boolean_attr(obj, name: str):
    if getattr(obj, name):
        return f"[green]{name}[/green]"
    else:
        return f"[red]{name}[/red]"
