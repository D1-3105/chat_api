# local
from chat_api.api import Base
# sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from sqlalchemy import select, or_
# python
import hashlib
import base64
import typing

if typing.TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class User(Base):
    __tablename__ = 'users'
    __table_args__ = UniqueConstraint('email', 'login'), {'extend_existing': True}
    extend_existing = True
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)
    login = Column(String)
    is_active = Column(Boolean, index=True, default=True)

    @classmethod
    async def filter_by_credentials(cls, session: 'AsyncSession', email=None, login=None):
        clauses = []
        if isinstance(email, str):
            clauses.append(cls.email == email)
        if isinstance(login, str):
            clauses.append(User.login == login)
        stmt = select(cls).where(or_(*clauses))
        return await session.scalars(stmt)

    def __repr__(self):
        return f'User:<{id=}>'

    def __eq__(self, other: typing.Optional['User']):
        if isinstance(other, User):
            return self.id == other.id
        elif isinstance(other, None):
            return False
        raise ValueError(f'Expected Optional[User], got: {other=}')

    def set_password(self, value: str | bytes) -> None:
        hashed_password = self.prepare_password(value)
        self.password = hashed_password

    def check_password(self, on_check: str | bytes) -> bool:
        hashed = self.prepare_password(on_check)
        return self.password == hashed

    @staticmethod
    def prepare_password(value: str | bytes):
        hashed = None
        if isinstance(value, bytes):
            hashed = hashlib.sha256(value).digest()
        if isinstance(value, str):
            hashed = hashlib.sha256(value.encode()).digest()
        return base64.b64encode(hashed).decode()


class JWTBlackList(Base):
    __tablename__ = 'JWTBlackList'
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True)
    key = Column(Integer, index=True)
