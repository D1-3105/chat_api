# local
from chat_api.api.conf.db import get_async_ses
from . import app
from .serializers import Credentials
from loggers import auth_logger as logger
# shortcuts
from shortcuts.encryption.encryption import JWT
# pydantic
from pydantic import StrictStr
# fastapi
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi import Depends
#
from .models import User

import typing

if typing.TYPE_CHECKING:
    from .models import User
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.engine.result import ScalarResult


class Authenticator:
    credentials: dict

    def __init__(self, async_session: 'AsyncSession', credentials: Credentials | dict):
        self.credentials = credentials
        self.async_session = async_session

    @classmethod
    def __exec_incorrect_type(cls):
        return HTTPException(status_code=422, detail='Credentials must be map')

    async def _afilter_users(self) -> 'ScalarResult[User]':

        """
        Filters users by credentials
        :return: Scalar of users
        """

        if isinstance(self.credentials, Credentials):
            filtered_users = await User.filter_by_credentials(self.async_session,
                                                              **self.credentials.dict(exclude={'password'}))
        elif isinstance(self.credentials, dict):
            filtered_users = await User.filter_by_credentials(
                self.async_session,
                email=self.credentials.get('email'),
                login=self.credentials.get('login')
            )
        else:
            raise self.__exec_incorrect_type()
        return filtered_users

    async def _acreate_user(self):
        """
        Creates user with given credentials
        :return:
        """
        if isinstance(self.credentials, Credentials):
            user = User(
                **self.credentials.dict(exclude={'password'})
            )
            raw_password = self.credentials.dict()['password']
        elif isinstance(self.credentials, dict):
            creds = self.credentials.copy()
            raw_password = creds.pop('password')
            user = User(
                **creds
            )
        else:
            raise self.__exec_incorrect_type()
        user.set_password(raw_password)
        self.async_session.add(user)

        return user

    @property
    async def user_and_marker(self) -> tuple['User', bool]:
        """
        if user exists then return User, False
        else return User, True
        :return:
        """
        if user := (await self._afilter_users()).one_or_none():
            created = False
        else:
            user = await self._acreate_user()
            created = True
        return user, created


@app.post(
    path='/register/'
)
async def get_or_create_user_route(credentials: Credentials):
    async_session: 'AsyncSession' = await get_async_ses()
    authenticator = Authenticator(async_session, credentials)
    user, created = await authenticator.user_and_marker
    jwt_object = JWT(
        data_to_encrypt={
            'user_id': user.id,
        }
    )
    encrypted_token, created_at = jwt_object.perform_encoding()
    if created:
        await async_session.commit()
    return JSONResponse(content={'token': encrypted_token, 'created_at': created_at}, status_code=200 + created)
