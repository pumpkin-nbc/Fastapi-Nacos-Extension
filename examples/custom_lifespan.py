"""FastAPI-Nacos-Extension composes an application's existing lifespan."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi_nacos_extension import FastAPINacos


@asynccontextmanager
async def application_lifespan(app: FastAPI):
    app.state.ready = True
    yield
    app.state.ready = False


app = FastAPI(lifespan=application_lifespan)
nacos = FastAPINacos(
    app,
    {
        "NACOS_SERVICE_NAME": "lifespan-api",
        "NACOS_SERVICE_IP": "127.0.0.1",
        "NACOS_SERVICE_PORT": 8002,
    },
)
