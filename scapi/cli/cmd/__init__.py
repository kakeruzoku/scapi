import typer

from . import account, proxy

typers: list[typer.Typer] = [
    account.app,
    proxy.app,
]


def add_typer(app: typer.Typer):
    for t in typers:
        app.add_typer(t)
