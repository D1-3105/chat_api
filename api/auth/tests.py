import unittest
from . import app
from fastapi.testclient import TestClient
from .models import User
from conf.db import get_async_ses
from .controllers import Authenticator, get_or_create_user_route
from .serializers import Credentials
import typing
from chat_api.api import loggers
import os

if typing.TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def test_credentials_serializer():
    credentials = {
        'login': 'user13414',
        'password': '12345678910'
    }
    credentials_serializer = Credentials(**credentials)
    assert credentials_serializer.dict() is not None


class TestFiltering(unittest.IsolatedAsyncioTestCase):

    """
        Tests asynchronous filtering
    """

    async def asyncSetUp(self) -> None:
        self.async_ses: 'AsyncSession' = await get_async_ses()
        self.credentials = {
            'login': 'user13414'
        }
        self.user_instance = User(
            login=self.credentials.get('login'),
            email=self.credentials.get('email')
        )
        self.user_instance.set_password('123123123')
        self.async_ses.add(self.user_instance)
        await self.async_ses.commit()

    async def test_filter_credentials(self):
        users_scalar = await User.filter_by_credentials(self.async_ses, **self.credentials)
        user = users_scalar.first()
        self.assertEqual(user, self.user_instance)

    async def asyncTearDown(self) -> None:
        await self.async_ses.delete(
            self.user_instance
        )
        await self.async_ses.commit()
        await self.async_ses.flush()
        await self.async_ses.rollback()
        await self.async_ses.close()


class TestRoutes(unittest.IsolatedAsyncioTestCase):

    client = TestClient(app)

    async def asyncSetUp(self) -> None:
        self.async_ses = await get_async_ses()
        self.credentials = {
            'login': 'user13414',
            'password': '1234567890'
        }

    async def test_authenticator_object(self):
        authenticator_instance = Authenticator(self.async_ses, self.credentials)
        user1, created1 = await authenticator_instance.user_and_marker
        user2, created2 = await authenticator_instance.user_and_marker
        self.assertEqual(user1, user1)
        self.assertTrue(created1)
        self.assertTrue(created2)

    async def test_authenticate_func(self):
        result = await get_or_create_user_route(self.credentials)
        self.assertEqual(result.status_code, 201)

    def test_user_creation(self):
        response = self.client.post(
            url='/register/',
            data=self.credentials
        )
        self.assertEqual(response.status_code, 201, msg=f'{response.status_code=}')

    async def asyncTearDown(self) -> None:
        user_scalar = await User.filter_by_credentials(
            self.async_ses,
            self.credentials.get('email'),
            self.credentials.get('login')
        )
        if user_instance := user_scalar.first():
            await self.async_ses.delete(user_instance)
        await self.async_ses.commit()



