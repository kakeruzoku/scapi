from typing import Annotated

from rich.table import Table
from sqlmodel import select
import typer
import scapi

from ..utils.asyncwrapper import async_wrapper
from ..utils.state import get_state
from ..utils.common import console, show_error
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
                f"✅ Proxy changed to {proxy.to_text} ."
            )


@app.command()
@async_wrapper
async def list(
    show_password: Annotated[bool, typer.Option(
        "--show-password/--hide-password", "-p"
    )] = False,
):
    async with get_state() as state:
        proxies = (await state.asyncsession.exec(select(ProxyTable))).all()
        table = Table(title=f"Your proxies: {len(proxies)}")

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
    name: Annotated[str | None, typer.Argument()] = None,
):
    async with get_state() as state:
        if name is None:
            state.config.use_proxy_id = None
            await state.config.save()
            console.print(
                f"✅ Proxy changed to [red]not use[/red] ."
            )
            return
        proxy = await ProxyTable.get(state.asyncsession, name)
        state.config.use_proxy_id = proxy.id
        await state.config.save()
        console.print(f"✅ Proxy changed to {proxy.to_text} .")


@app.command()
@async_wrapper
async def delete(
    name: Annotated[str | None, typer.Argument()] = None,
):
    async with get_state() as state:
        if name is None:
            proxy = state._proxy
            if proxy is None:
                show_error(ValueError(), "No proxy selected.")
        else:
            proxy = await ProxyTable.get(state.asyncsession, name)

        await state.asyncsession.delete(proxy)
        await state.asyncsession.commit()
        console.print(
            f"✅ Proxy {proxy.to_text} has been removed."
        )
        if state._proxy and proxy == state._proxy:
            await change()
