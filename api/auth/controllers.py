# local
from chat_api.api.conf.db import make_endpoint_ses
from . import app
from .serializers import Credentials, BearerToken, UserProfile
# shortcuts
from shortcuts.encryption.encryption import JWT, JWTException, DecodeError
# pydantic
# fastapi
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi import Depends, Request
#
from .models import User

import typing
import datetime

if typing.TYPE_CHECKING:
    from .models import User
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.engine.result import ScalarResult


class Authenticator:
    credentials: dict

    def __init__(self, async_session: 'AsyncSession', credentials: Credentials | dict):
        self.credentials = credentials
        self.async_session = async_session

    @staticmethod
    async def verify_token(req: Request):
        token = req.headers.get('Authorization')
        if not isinstance(token, str):
            raise HTTPException(status_code=400)
        prefix, *encrypted = token.split()
        if isinstance(encrypted, list):
            encrypted = ''.join(encrypted)
        try:
            decrypted = JWT.decrypt(encrypted)
        except JWTException() as je:
            raise HTTPException(status_code=403, detail={'error': 'Token expired!'})
        except DecodeError() as de:
            raise HTTPException(status_code=401, detail={'error': 'Invalid token'})
        return decrypted

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

    @staticmethod
    async def aencrypt_user(user_instance: 'User'):
        jwt_object = JWT(
            data_to_encrypt={
                'user_id': user_instance.id,
            }
        )
        encrypted_token, expires = jwt_object.perform_encoding()
        return encrypted_token, expires

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
        user.is_active = True
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
            if not user.is_active:
                raise HTTPException(status_code=403, detail={'error': 'User inactive!'})
        assert user is not None

        return user, created


@app.post(
    path='/register/'
)
async def get_or_create_user_route(credentials: Credentials, async_session=Depends(make_endpoint_ses)):
    authenticator = Authenticator(async_session, credentials)
    user, created = await authenticator.user_and_marker
    if created:
        await async_session.flush()
    encrypted_token, expires = await authenticator.aencrypt_user(user)
    if created:
        await async_session.commit()
    return JSONResponse(content={'token': encrypted_token, 'expire_at': expires}, status_code=200 + created)


@app.get(
    path='/user/profile/',
    response_model=UserProfile
)
async def obtain_user_data(
        async_ses=Depends(make_endpoint_ses),
        user_data=Depends(Authenticator.verify_token),
):
    user_data: dict
    user_id = user_data.get('user_id')
    async_ses: 'AsyncSession'
    user_instance = await async_ses.get(
        User, {'id': user_id}
    )
    return UserProfile(
        email=user_instance.email,
        login=user_instance.login,
        id=user_instance.id
    )
