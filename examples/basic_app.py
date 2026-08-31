"""Minimal FastAPI-Nacos application."""

from fastapi import FastAPI

from fastapi_nacos import FastAPINacos

app = FastAPI(title="FastAPI-Nacos basic example")
nacos = FastAPINacos(
    app,
    {
        "NACOS_SERVER_ADDR": "127.0.0.1:8848",
        "NACOS_SERVICE_NAME": "basic-api",
        "NACOS_SERVICE_IP": "127.0.0.1",
        "NACOS_SERVICE_PORT": 8000,
        "NACOS_AUTO_REGISTER": True,
    },
)


@app.get("/")
async def index():
    return {"service": "basic-api", "nacos": nacos.get_status(app)}

