from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

# DATABASES
DEBUG = True
SECRET_KEY = 'asdwerfsZfadhgaqefssafsaftrkyFRSADQWRdadwtefa234rsfty54ueysd_xcpwfe[rwpdafg'
JWT_ACCESS_TTL = 5*60*60  # time to live for json token
assert len(SECRET_KEY) > 32
app = FastAPI(debug=DEBUG)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Custom title",
        version="2.5.0",
        description="This is a very custom OpenAPI schema",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi_schema = custom_openapi
