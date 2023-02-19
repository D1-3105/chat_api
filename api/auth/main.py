from chat_api.api import auth
from loggers import config
import uvicorn


if __name__ == '__main__':
    uvicorn.run(auth.app, host='0.0.0.0', port=8001, log_config=config)
