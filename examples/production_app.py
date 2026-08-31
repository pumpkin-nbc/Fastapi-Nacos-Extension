"""Complete configuration suitable for multi-worker deployment."""

import os

from fastapi import FastAPI

from fastapi_nacos import FastAPINacos

app = FastAPI(title="FastAPI-Nacos production example")
nacos = FastAPINacos(
    app,
    {
        "NACOS_SERVER_ADDR": os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
        "NACOS_NAMESPACE_ID": os.getenv("NACOS_NAMESPACE_ID", ""),
        "NACOS_USERNAME": os.getenv("NACOS_USERNAME"),
        "NACOS_PASSWORD": os.getenv("NACOS_PASSWORD"),
        "NACOS_SERVICE_NAME": "production-api",
        "NACOS_SERVICE_IP": os.getenv("SERVICE_IP", "127.0.0.1"),
        "NACOS_SERVICE_PORT": int(os.getenv("SERVICE_PORT", "8000")),
        "NACOS_SERVICE_GROUP": "DEFAULT_GROUP",
        "NACOS_SERVICE_CLUSTER": os.getenv("SERVICE_CLUSTER", "DEFAULT"),
        "NACOS_SERVICE_METADATA": {"version": "0.1.0", "pid": str(os.getpid())},
        "NACOS_AUTO_REGISTER": True,
        "NACOS_DEREGISTER_ON_EXIT": True,
        "NACOS_RETRY_ENABLED": True,
        "NACOS_RETRY_TIMES": 3,
        "NACOS_RETRY_INTERVAL": 1.0,
        "NACOS_HEALTH_CHECK_ENABLED": True,
        "NACOS_LOG_ENABLED": True,
        "NACOS_LOG_CONSOLE_ENABLED": True,
        "NACOS_LOG_FILE_ENABLED": False,
    },
)


@app.get("/")
async def root():
    return {"service": "production-api", "pid": os.getpid()}

