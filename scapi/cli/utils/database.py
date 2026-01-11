
from contextlib import asynccontextmanager
from typing import Self
import aiohttp
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Column, Field, SQLModel, String, select
import scapi

from .middleware import ErrorMiddleware
from .error import CliNotFound
from .common import app_dir, console, show_error


database_path = app_dir / "database.sqlite3"

engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")


class SessionTable(SQLModel, table=True):
    __tablename__ = "session"  # pyright: ignore[reportAssignmentType]

    user_id: int = Field(primary_key=True)
    username: str = Field(
        sa_column=Column(String(collation="NOCASE"), index=True)
    )
    session_id: str

    @classmethod
    def from_session(cls, scapi_session: scapi.Session) -> Self:
        assert scapi_session.user_id
        return cls(
            user_id=scapi_session.user_id,
            username=scapi_session.username,
            session_id=scapi_session.session_id
        )

    @property
    def to_text(self):
        return f"[b blue]@{self.username}[/b blue] (ID:#{self.user_id})"

    @classmethod
    async def get_or_none(cls, asyncsession: AsyncSession, username: str) -> "SessionTable | None":
        stmt = select(SessionTable).where(SessionTable.username == username)
        return (await asyncsession.exec(stmt)).first()

    @classmethod
    async def get(cls, asyncsession: AsyncSession, username: str) -> "SessionTable":
        session = await cls.get_or_none(asyncsession, username)
        if session is None:
            show_error(
                CliNotFound(),
                f"Account [b blue]@{username}[/b blue] is not found."
            )
        return session

    @classmethod
    async def add_session(cls, asyncsession: AsyncSession, scapi_session: scapi.Session) -> Self:
        session = cls.from_session(scapi_session)
        asyncsession.add(session)
        with ErrorMiddleware({
            IntegrityError: (f"Account: {session.to_text} already exists.")
        }):
            await asyncsession.commit()
        console.print(
            f"✅ Logged in as {session.to_text}."
        )
        return session


class ProxyTable(SQLModel, table=True):
    __tablename__ = "proxy"  # pyright: ignore[reportAssignmentType]

    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    url: str
    username: str | None
    password: str | None

    @property
    def to_text(self):
        return self.name

    def set_proxy(self):
        auth = None if self.username is None else aiohttp.BasicAuth(
            self.username, self.password or "")
        scapi.set_default_proxy(self.url, auth)

    @classmethod
    async def get_or_none(cls, asyncsession: AsyncSession, name: str) -> "ProxyTable | None":
        stmt = select(ProxyTable).where(ProxyTable.name == name)
        return (await asyncsession.exec(stmt)).first()

    @classmethod
    async def get(cls, asyncsession: AsyncSession, name: str) -> "ProxyTable":
        session = await cls.get_or_none(asyncsession, name)
        if session is None:
            show_error(
                CliNotFound(),
                f"Proxy [b]{name}[/b] is not found."
            )
        return session


async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def create_asyncsession():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        with session.no_autoflush:
            yield session
