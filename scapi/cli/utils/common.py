from pathlib import Path
from typing import NoReturn
import click
from rich.console import Console

from rich.panel import Panel
import typer

APP_NAME = "scapi"

console = Console()

app_dir = Path(typer.get_app_dir(APP_NAME)).resolve()


def create_app_folder():
    app_dir.mkdir(parents=True, exist_ok=True)


class CustomError(click.ClickException):
    def __init__(self, *messages):
        super().__init__("\n".join(messages))
