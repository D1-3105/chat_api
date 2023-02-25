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
            'login': 'user13414',
            'email': '1234@gmail.com'
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
            'email': '123@gmail.com',
            'password': '1234567890'
        }

    async def test_authenticator_object(self):
        authenticator_instance = Authenticator(self.async_ses, self.credentials)
        user1, created1 = await authenticator_instance.user_and_marker
        user2, created2 = await authenticator_instance.user_and_marker
        self.assertEqual(user1, user1)
        self.assertTrue(created1)
        self.assertTrue(created2)
        self.addAsyncCleanup(
            self.cleanup_user,
            email=self.credentials.get('email')
        )

    async def test_user_creation(self):
        create_response = self.client.post(
            url='/register/',
            json=self.credentials
        )
        self.assertTrue(create_response.status_code >= 200, msg=f'{create_response.status_code=}')
        self.addAsyncCleanup(
            self.cleanup_user,
            email=self.credentials.get('email')
        )

    async def test_get_user_profile(self):
        authenticator = Authenticator(self.async_ses, self.credentials)
        user, created = await authenticator.user_and_marker
        if created:
            await self.async_ses.commit()
            self.async_ses.refresh(user)
        self.addAsyncCleanup(
            self.cleanup_user,
            email=self.credentials.get('email')
        )
        token, _ = await authenticator.aencrypt_user(user)
        profile_response = self.client.get(
            url='/user/profile',
            headers={'Authorization': f'Bearer {token}'}
        )
        self.assertIn('id', profile_response.json())

    @staticmethod
    async def cleanup_user(**credentials):
        teardown_ses = await get_async_ses()
        user_scalar = await User.filter_by_credentials(
            teardown_ses,
            **credentials
        )
        if user_instance := user_scalar.first():
            await teardown_ses.delete(user_instance)
        await teardown_ses.commit()
        await teardown_ses.close()

    async def asyncTearDown(self) -> None:
        self.async_ses.close()



