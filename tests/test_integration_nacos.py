"""Opt-in smoke test against a disposable Nacos 2.3.2 server."""

import asyncio
import os
import time
import uuid

import pytest
from fastapi import FastAPI

from fastapi_nacos_extension import FastAPINacos

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("NACOS_INTEGRATION") != "1",
        reason="set NACOS_INTEGRATION=1 to use the disposable Nacos server",
    ),
]


async def wait_for(extension, app, key, expected, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if extension.get_status(app)[key] is expected:
            return
        await asyncio.sleep(0.05)
    raise AssertionError("Nacos lifecycle did not converge before timeout")


@pytest.mark.anyio
async def test_register_discover_config_surface_and_deregister():
    service_name = "fastapi-nacos-integration-" + uuid.uuid4().hex[:8]
    app = FastAPI()
    extension = FastAPINacos(
        app,
        {
            "NACOS_SERVER_ADDR": os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848"),
            "NACOS_SERVICE_NAME": service_name,
            "NACOS_SERVICE_IP": "127.0.0.1",
            "NACOS_SERVICE_PORT": 18080,
            "NACOS_AUTO_REGISTER": False,
            "NACOS_DEREGISTER_ON_EXIT": False,
            "NACOS_RETRY_INTERVAL": 0.1,
        },
    )

    try:
        await extension.register_instance(app)
        await wait_for(extension, app, "registered", True)
        instances = await extension.list_instances(app, service_name)
        assert any(
            row["ip"] == "127.0.0.1" and row["port"] == 18080
            for row in instances
        )
        assert await extension.get_config(app, "fastapi-nacos-missing") is None
    finally:
        assert await extension.deregister_instance(app)
        await wait_for(extension, app, "registered", False)
