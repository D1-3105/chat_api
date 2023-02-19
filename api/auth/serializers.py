import logging

from pydantic import (
    BaseModel,
    StrictStr,
    EmailStr,
    Field,
    root_validator
)
from typing import Optional
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
