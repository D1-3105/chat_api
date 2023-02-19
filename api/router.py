from chat_api.api.conf.config import app
from pydantic import StrictStr


@app.get('/register/')
async def make_register(credentials:dict[StrictStr]):
    ...
