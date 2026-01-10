
from contextlib import asynccontextmanager
from typing import Self
import aiohttp
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import Column, Field, SQLModel, String
import scapi

from .common import app_dir


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
    def from_session(cls, session: scapi.Session) -> Self:
        assert session.user_id
        return cls(
            user_id=session.user_id,
            username=session.username,
            session_id=session.session_id
        )

    @property
    def to_text(self):
        return f"[b blue]@{self.username}[/b blue] (ID:#{self.user_id})"


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


async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@asynccontextmanager
async def create_asyncsession():
    async with AsyncSession(engine, expire_on_commit=False) as session:
        with session.no_autoflush:
            yield session
