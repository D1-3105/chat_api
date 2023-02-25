import abc

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker

import typing

if typing.TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy.orm import Session

SQLALCHEMY_DATABASE_URL = 'postgresql+asyncpg://chat_user:postgres@localhost:5432/chat_db'
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, echo=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=True
)


BASE_PARENT: 'DeclarativeBase.__class__' = declarative_base()

Base = BASE_PARENT


def get_ses():
    return SessionLocal()


async def get_async_ses():
    return async_sessionmaker(engine)()


async def make_endpoint_ses():
    async with async_sessionmaker(engine)() as ses:
        yield ses

"""
class Base(BASE_PARENT, abc.ABC):
    __table_args__ = {'extend_existing': True}
"""
