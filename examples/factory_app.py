"""Application-factory pattern."""

from fastapi import FastAPI

from fastapi_nacos_extension import FastAPINacos

nacos = FastAPINacos(config={"NACOS_SERVER_ADDR": "127.0.0.1:8848"})


def create_app() -> FastAPI:
    app = FastAPI(title="Factory example")
    nacos.init_app(
        app,
        {
            "NACOS_SERVICE_NAME": "factory-api",
            "NACOS_SERVICE_IP": "127.0.0.1",
            "NACOS_SERVICE_PORT": 8001,
            "NACOS_HEALTH_CHECK_ENABLED": True,
        },
    )
    return app


app = create_app()
