import typer
from . import cmd

help_text = f"""\
Run Scapi on the command line."""

app = typer.Typer(help=help_text)

cmd.add_typer(app)


@app.callback()
def callback():
    """
    Run Scapi on the command line.
    """
