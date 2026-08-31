"""Shared fixtures that keep the test suite completely offline."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI

import fastapi_nacos_extension.extension as extension_module
import fastapi_nacos_extension.retry as retry_module


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch):
    monkeypatch.setattr(retry_module, "_sleep", lambda *_args, **_kwargs: None)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def fake_client():
    client = MagicMock(name="NacosClient")
    client.default_timeout = 0.1
    client.add_naming_instance.return_value = True
    client.remove_naming_instance.return_value = True
    client.list_naming_instance.return_value = {
        "hosts": [
            {
                "ip": "127.0.0.1",
                "port": 8000,
                "healthy": True,
                "weight": 1.0,
                "clusterName": "DEFAULT",
                "metadata": {"version": "v1"},
            },
            {
                "ip": "127.0.0.1",
                "port": 8001,
                "healthy": True,
                "weight": 2.0,
                "clusterName": "CANARY",
                "metadata": {"version": "v2"},
            },
        ]
    }
    client.get_config.return_value = "server:\n  port: 8000\n"
    client.send_heartbeat.return_value = True
    return client


@pytest.fixture
def patched_create_client(monkeypatch, fake_client):
    calls = {"count": 0, "configs": []}

    def factory(config):
        calls["count"] += 1
        calls["configs"].append(dict(config))
        return fake_client

    monkeypatch.setattr(extension_module, "create_client", factory)
    return calls


@pytest.fixture
def base_config():
    return {
        "NACOS_SERVER_ADDR": "127.0.0.1:8848",
        "NACOS_SERVICE_NAME": "test-service",
        "NACOS_SERVICE_IP": "127.0.0.1",
        "NACOS_SERVICE_PORT": 8000,
        "NACOS_AUTO_REGISTER": False,
        "NACOS_DEREGISTER_ON_EXIT": False,
        "NACOS_RETRY_INTERVAL": 0,
    }


@pytest.fixture
def make_app(base_config):
    def factory(overrides=None, *, use_base=True, lifespan=None):
        config = dict(base_config) if use_base else {}
        config.update(overrides or {})
        return FastAPI(lifespan=lifespan), config

    return factory
