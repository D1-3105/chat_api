from chat_api.api.conf.config import (
    SECRET_KEY,
    JWT_ACCESS_TTL
)
from typing import Optional, Any
import typing
import jwt
import datetime
import json


class JWTException(Exception):
    ...


class JWT:
    date_format = '%Y/%d/%m %H:%M:%S'
    token_ttl = JWT_ACCESS_TTL

    def __init__(self, data_to_encrypt: Any = None, lifetime=JWT_ACCESS_TTL):
        self.token_ttl = lifetime
        if data_to_encrypt:
            self._construct_encrypt(data_to_encrypt)

    @classmethod
    def decrypt(cls, token: Optional[str] = None):
        decoded_data = jwt.decode(token, SECRET_KEY, options={"verify_signature": False})
        expire = datetime.datetime.strptime(decoded_data['expire'], cls.date_format)
        if expire < datetime.datetime.now():
            raise JWTException('JWT token expired!')
        return json.loads(decoded_data['data'])

    def _construct_encrypt(self, data_to_encrypt):
        jsoned_data: str = json.dumps(data_to_encrypt)
        date_expire = datetime.datetime.now() + datetime.timedelta(seconds=self.token_ttl)
        self.expire: str = date_expire.strftime(self.date_format)
        self.data = {'data': jsoned_data, 'expire': self.expire}

    def perform_encoding(self):
        encoded = jwt.encode(payload=self.data, key=SECRET_KEY)
        return encoded, self.expire
