from fastapi.exceptions import HTTPException
from pydantic import (
    BaseModel,
    StrictStr,
    EmailStr,
    Field,
    root_validator,
    validator
)
from typing import Optional, FrozenSet
from loggers import auth_logger as logger


class Credentials(BaseModel):
    password: StrictStr = Field(min_length=10)
    email: EmailStr
    login: Optional[StrictStr]

    @root_validator
    def validate_fields(cls, field_values):
        logger.debug(f'{field_values=}')
        assert field_values.get('email') or field_values.get('login')
        return field_values


class BearerToken(BaseModel):
    auth: StrictStr

    @classmethod
    @validator('token')
    def validate_token(cls, value, **kwargs):
        prefix, *token = value.split()
        ''.join(token)
        if prefix != 'Bearer':
            raise HTTPException(status_code=400, detail={'Error': 'Bearer missing'})
        return token


class UserProfile(BaseModel):
    id: int
    login: str | None
    email: EmailStr

