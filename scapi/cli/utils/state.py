

from typing import Self
from contextlib import AsyncExitStack, asynccontextmanager

from rich.panel import Panel
import typer

import scapi

from .common import create_app_folder, show_error, console
from .database import ProxyTable, SessionTable, create_asyncsession, setup_database
from .config import Config


class State:
    async def init(self, stack: AsyncExitStack) -> Self:
        global state
        state = self

        self.asyncsession = await stack.enter_async_context(create_asyncsession())
        self.config = await Config.get_config()

        proxy_id = self.config.use_proxy_id
        self._proxy = None
        if proxy_id:
            proxy = await self.asyncsession.get(ProxyTable, proxy_id)
            if proxy is None:
                self.config.use_proxy_id = None
                await self.config.save()
                raise show_error(
                    ValueError(),
                    f"The specified proxy:#{proxy_id} does not exist in the database."
                )
            proxy.set_proxy()
            self._proxy = proxy
            console.print(f"📄 Proxy: {proxy.to_text} in use")

        self.session = self._session = None
        user_id = self.config.use_user_id
        if user_id:
            session = await self.asyncsession.get(SessionTable, user_id)
            if session is None:
                self.config.use_user_id = None
                await self.config.save()
                raise show_error(
                    ValueError(),
                    f"The specified account:#{user_id} does not exist in the database."
                )
            self._session = session
            self.session = await stack.enter_async_context(scapi.Session(session.session_id))
            console.print(f"📄 Account: {session.to_text} in use")

        self.stack = stack
        return self


state: State | None = None


@asynccontextmanager
async def get_state():
    global state
    if state:
        yield state
        return
    async with AsyncExitStack() as stack:
        create_app_folder()
        await setup_database()
        try:
            yield await State().init(stack)
        except Exception as e:
            if e is None:
                return
            if isinstance(e, scapi.exceptions.HTTPError):
                text = []
                match e:
                    case scapi.exceptions.IPBanned():
                        text = (
                            f"Your IP: [b]{e.ip}[/b] is blocked.",
                        )
                    case scapi.exceptions.AccountBlocked():
                        text = (
                            f"This account is blocked.",
                        )
                    case scapi.exceptions.LoginFailure():
                        text = (
                            f"Login to [b blue]@{e.username}[/b blue] failed. Number of attempts: {e.num_tries or 'unknown'}.",
                            f"message: {e.message}",
                        )
                        if e.request_capture:
                            text = (
                                *text,
                                f"[b red]reCAPTCHA is required to log in.[/b red]"
                            )
                    case scapi.exceptions.ResponseError():
                        text = (
                            f"Status code: {e.status_code} was returned.",
                            f"content: {e.response.text}"
                        )
                raise show_error(e, text)
            raise
