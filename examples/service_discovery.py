"""Cluster/metadata discovery and weighted selection."""

from fastapi import FastAPI

from fastapi_nacos_extension import FastAPINacos

app = FastAPI()
nacos = FastAPINacos(app, {"NACOS_AUTO_REGISTER": False})


@app.get("/payments")
async def payments():
    return await nacos.list_instances(
        app,
        "payments-api",
        healthy_only=True,
        cluster="BLUE",
        metadata={"region": "cn-east"},
    )


@app.get("/payments/one")
async def one_payment():
    return await nacos.get_one_healthy_instance(
        app, "payments-api", strategy="weight"
    )
