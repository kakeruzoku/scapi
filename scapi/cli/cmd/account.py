from typing import Annotated
from rich.table import Table
from sqlmodel import select
import typer

import scapi

from ..utils.asyncwrapper import async_wrapper
from ..utils.state import get_state
from ..utils.common import console, show_error, boolean_attr
from ..utils.middleware import ErrorMiddleware, ProgressMiddleware
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
        if await SessionTable.get_or_none(state.asyncsession, username):
            show_error(
                ValueError(),
                f"Account: [b blue]@{username}[/b blue] already exists."
            )
        with ProgressMiddleware() as progress:
            with progress.add_task(f"Logging in to [b blue]@{username}[/b blue] with password"):
                scapi_session = await scapi.login(username, password, recaptcha_code=recaptcha_code)
            session = await SessionTable.add_session(state.asyncsession, scapi_session)
        if switch:
            state.config.use_user_id = session.user_id
            await state.config.save()
            console.print(
                f"✅ Account changed to {session.to_text}."
            )


@app.command()
@async_wrapper
async def add(
    session_id: Annotated[str, typer.Argument()],
    switch: Annotated[bool, typer.Option(
        "--switch/--no-switch", "-s"
    )] = False,
):
    async with get_state() as state:
        with ErrorMiddleware({
            Exception: "Failed to parse session."
        }):
            async with scapi.Session(session_id) as scapi_session:
                pass
        session = await SessionTable.add_session(state.asyncsession, scapi_session)
        if switch:
            state.config.use_user_id = session.user_id
            await state.config.save()
            console.print(
                f"✅ Account changed to {session.to_text}."
            )


@app.command()
@async_wrapper
async def list():
    async with get_state() as state:
        sessions = (await state.asyncsession.exec(select(SessionTable))).all()
        table = Table(title=f"Your accounts: {len(sessions)}")

        table.add_column("username")
        table.add_column("user_id")

        for s in sessions:
            row = [s.username, str(s.user_id)]
            table.add_row(*row)

        console.print(table)


@app.command()
@async_wrapper
async def change(
    username: Annotated[str | None, typer.Argument()] = None,
):
    username = username and username.removeprefix("@")
    async with get_state() as state:
        if username is None:
            state.config.use_user_id = None
            await state.config.save()
            console.print(
                f"✅ Account changed to [red]not use[/red] ."
            )
            return
        session = await SessionTable.get(state.asyncsession, username)
        state.config.use_user_id = session.user_id
        await state.config.save()
        console.print(f"✅ Account changed to {session.to_text} .")


@app.command()
@async_wrapper
async def show(
    username: Annotated[str | None, typer.Argument()] = None,
    user_id: Annotated[str | None, typer.Option(
        "--user-id", "--id", "-i"
    )] = None,
    show_session_id: Annotated[bool, typer.Option(
        "--show-session-id/--hide-session-id", "-s"
    )] = False,
    get_info: Annotated[bool, typer.Option(
        "--get-info/--no-get-info", "-g"
    )] = False,
):
    username = username and username.removeprefix("@")
    async with get_state() as state:
        session: SessionTable | None = None
        scapi_session: scapi.Session | None = None
        if username is None:
            if user_id is None:
                session = state._session
                scapi_session = state.session
            else:
                session = await state.asyncsession.get(SessionTable, user_id)
        else:
            if user_id is None:
                session = await SessionTable.get(state.asyncsession, username)
            else:
                show_error(
                    ValueError(),
                    "You cannot specify both username and user_id at the same time."
                )

        if session is None:
            show_error(
                ValueError(),
                "Failed to obtain a session."
            )
        if scapi_session is None:
            scapi_session = await state.stack.enter_async_context(scapi.Session(session.session_id))

        if get_info:
            with ErrorMiddleware({
                scapi.exceptions.ClientError: (
                    "This session is invalid. Please log in again."
                ),
                scapi.exceptions.Forbidden: None,
            }):
                with ProgressMiddleware() as progress:
                    with progress.add_task(f"Loading account information..."):
                        await scapi_session.update()

        console.print("\n".join((
            f"About {session.to_text}",
            f"logged at {scapi_session.logged_at} / {scapi_session.login_ip}",
        )))

        status = scapi_session.status
        if status:
            console.print("\n".join((
                f"joined at {status.joined_at}",
                f"email: {status.email}",
                f"gender: {status.gender}",
                f"classroom_id: {status.classroom_id}"
            )))
            console.print("mute_status:", status.mute_status)

            boolean_attr_list = [
                "banned", "should_vpn", "admin", "scratcher", "scratcher", "invited_scratcher", "social", "educator", "educator_invitee", "student", "must_reset_password", "must_complete_registration", "has_outstanding_email_confirmation", "show_welcome", "confirm_email_banner", "unsupported_browser_banner", "with_parent_email", "project_comments_enabled", "gallery_comments_enabled", "userprofile_comments_enabled", "everything_is_totally_normal"
            ]

            console.print(
                "status: "+" ".join(
                    [boolean_attr(status, attr)for attr in boolean_attr_list]
                )
            )

        if show_session_id:
            console.print("\n".join((
                f"xtoken: {scapi_session.xtoken}",
                f"session_id: {scapi_session.session_id}",
            )), highlight=False)


@app.command()
@async_wrapper
async def logout(
    username: Annotated[str | None, typer.Argument()] = None,
    show_session_id: Annotated[bool, typer.Option(
        "--show-session-id/--hide-session-id", "-s"
    )] = False,
):
    username = username and username.removeprefix("@")
    async with get_state() as state:
        if username is None:
            session = state._session
            if session is None:
                show_error(ValueError(), "No account selected.")
        else:
            session = await SessionTable.get(state.asyncsession, username)

        await state.asyncsession.delete(session)
        await state.asyncsession.commit()
        console.print(
            f"✅ Account {session.to_text} has been logged out."
        )
        if show_session_id:
            console.print(
                f"session_id: {session.session_id}",
                highlight=False
            )
        if state._session and session == state._session:
            await change()
