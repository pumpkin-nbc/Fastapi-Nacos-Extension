"""Local-only health endpoint at /health/nacos."""

from fastapi import FastAPI

from fastapi_nacos_extension import FastAPINacos

app = FastAPI()
nacos = FastAPINacos(
    app,
    {
        "NACOS_AUTO_REGISTER": False,
        "NACOS_HEALTH_CHECK_ENABLED": True,
        "NACOS_HEALTH_CHECK_PATH": "/health/nacos",
    },
)


@app.get("/status")
async def status():
    return nacos.get_status(app)
