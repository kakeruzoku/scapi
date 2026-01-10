from typing import Annotated

from rich.table import Table
from sqlmodel import select
import typer
import scapi

from ..utils.asyncwrapper import async_wrapper
from ..utils.state import get_state
from ..utils.common import console
from ..utils.database import ProxyTable

app = typer.Typer(name="proxy")


@app.command()
@async_wrapper
async def add(
    url: Annotated[str, typer.Argument()],
    username: Annotated[str | None, typer.Option(
        "--username", "-u"
    )] = None,
    password: Annotated[str | None, typer.Option(
        "--password", "-p"
    )] = None,
    name: Annotated[str | None, typer.Option("--name", "-n")] = None,
    switch: Annotated[bool, typer.Option(
        "--switch/--no-switch", "-s")] = False,
):
    async with get_state() as state:
        proxy = ProxyTable(
            name=name or f"{url}@{username}",
            url=url,
            username=username,
            password=password,
        )
        state.asyncsession.add(proxy)
        await state.asyncsession.commit()
        console.print(
            f"✅ Proxy {proxy.name} added."
        )
        if switch:
            state.config.use_proxy_id = proxy.id
            await state.config.save()
            console.print(
                f"✅ Proxy changed to {proxy.to_text}."
            )


@app.command()
@async_wrapper
async def list(
    show_password: Annotated[bool, typer.Option(
        "--show-password/--hide-password", "-p"
    )] = False,
):
    async with get_state() as state:
        proxies = await state.asyncsession.exec(select(ProxyTable))
        table = Table(title="Your proxies")

        table.add_column("name")
        table.add_column("url")
        table.add_column("username")

        if show_password:
            table.add_column("password")

        for p in proxies:
            row = [p.name, p.url, p.username]
            if show_password:
                row.append(p.password)
            table.add_row(*row)

        console.print(table)


@app.command()
@async_wrapper
async def change(
    name: Annotated[str, typer.Argument()],
):
    async with get_state() as state:
        stmt = select(ProxyTable).where(ProxyTable.name == name)
        proxy = (await state.asyncsession.exec(stmt)).first()
        if proxy is None:
            raise typer.BadParameter(
                f"Proxy: {name} is not found.",
                param_hint="name"
            )
