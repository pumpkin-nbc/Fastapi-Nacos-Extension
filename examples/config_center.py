"""Raw configuration-center read."""

from fastapi import FastAPI, Response

from fastapi_nacos_extension import FastAPINacos

app = FastAPI()
nacos = FastAPINacos(
    app,
    {
        "NACOS_AUTO_REGISTER": False,
        "NACOS_CONFIG_DATA_ID": "application.yaml",
        "NACOS_CONFIG_GROUP": "DEFAULT_GROUP",
    },
)


@app.get("/configuration", response_class=Response)
async def configuration():
    content = await nacos.get_config(app)
    return Response(content=content or "", media_type="text/plain")
