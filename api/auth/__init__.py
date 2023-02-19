from chat_api.api.conf import app
from . import controllers

import logging

logger=logging.Logger(name='auth')
logger.addHandler(logging.FileHandler('auth.log'))

