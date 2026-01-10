from typing import Annotated
import typer

import scapi

from ..utils.asyncwrapper import async_wrapper
from ..utils.state import get_state
from ..utils.common import console
from ..utils.middleware import ProgressMiddleware
from ..utils.database import SessionTable

app = typer.Typer(name="account")


@app.command()
@async_wrapper
async def login(
    username: Annotated[str, typer.Argument()],
    password: Annotated[str, typer.Option(
        "--password", "-p", prompt=True, hide_input=True,
    )],
    switch: Annotated[bool, typer.Option(
        "--switch/--no-switch", "-s"
    )] = False,
    recaptcha_code: Annotated[str | None, typer.Option(
        "--recaptcha", "-r"
    )] = None
):
    """
    Log in to your Scratch account.
    """
    username = username.removeprefix("@")
    async with get_state() as state:
        with ProgressMiddleware() as progress:
            with progress.add_task(f"Logging in to [b blue]@{username}[/b blue] with password"):
                scapi_session = await scapi.login(username, password, recaptcha_code=recaptcha_code)
            session = SessionTable.from_session(scapi_session)
            state.asyncsession.add(session)
            await state.asyncsession.commit()
            console.print(
                f"✅ Logged in as {session.to_text}."
            )
        if switch:
            state.config.use_user_id = session.user_id
            await state.config.save()
            console.print(
                f"✅ Account changed to {session.to_text}."
            )
