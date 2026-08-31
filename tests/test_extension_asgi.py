"""FastAPI integration and public async API tests."""

import asyncio
import threading
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_nacos import FastAPINacos, FastAPINacosError, NacosValidationError
from fastapi_nacos.health import HEALTH_ENDPOINT
from tests.helpers import wait_registered, wait_until

STATUS_FIELDS = {
    "enabled",
    "pid",
    "client_created",
    "service_name",
    "group_name",
    "cluster_name",
    "service_ip",
    "service_port",
    "target_registered",
    "registered",
    "operation_running",
    "last_error",
    "heartbeat_state",
    "last_heartbeat_success_at",
    "last_heartbeat_failure_at",
    "heartbeat_error_type",
}


def test_init_is_lazy_idempotent_and_explicit(make_app, patched_create_client, fake_client):
    app, config = make_app()
    extension = FastAPINacos(app, config)
    original = app.state.nacos

    extension.init_app(app, {"NACOS_SERVICE_NAME": "ignored-on-repeat"})
    assert app.state.nacos is original
    assert extension.get_cached_client(app) is None
    assert patched_create_client["count"] == 0
    assert asyncio.run(extension.get_client(app)) is fake_client
    assert patched_create_client["count"] == 1
    with pytest.raises(FastAPINacosError, match="explicit"):
        extension.get_status(None)


def test_state_collision_and_wrong_owner(make_app):
    app, config = make_app()
    app.state.nacos = object()
    with pytest.raises(FastAPINacosError, match="already owned"):
        FastAPINacos(app, config)

    other, other_config = make_app()
    first = FastAPINacos(other, other_config)
    second = FastAPINacos()
    with pytest.raises(FastAPINacosError, match="already owned"):
        second.init_app(other, other_config)
    with pytest.raises(FastAPINacosError, match="not owned"):
        second.get_status(other)
    assert first.get_status(other)["enabled"] is True


def test_disabled_mode_never_creates_client(make_app, patched_create_client):
    app, config = make_app({"NACOS_ENABLED": False})
    extension = FastAPINacos(app, config)
    assert asyncio.run(extension.get_client(app)) is None
    assert asyncio.run(extension.list_instances(app, "orders")) == []
    assert asyncio.run(extension.get_config(app, "settings")) is None
    assert set(extension.get_status(app)) == STATUS_FIELDS
    assert extension.get_status(app)["heartbeat_state"] == "not_applicable"
    assert patched_create_client["count"] == 0


@pytest.mark.anyio
async def test_public_discovery_selection_and_config(
    make_app, patched_create_client, fake_client
):
    app, config = make_app({"NACOS_CONFIG_DATA_ID": "application.yaml"})
    extension = FastAPINacos(app, config)

    rows = await extension.list_instances(
        app, "orders", cluster="CANARY", metadata={"version": "v2"}
    )
    assert [(row["ip"], row["port"]) for row in rows] == [("127.0.0.1", 8001)]
    chosen = await extension.get_one_healthy_instance(app, "orders", strategy="first")
    assert chosen["port"] == 8000
    assert await extension.get_config(app) == "server:\n  port: 8000\n"
    fake_client.get_config.assert_called_with(
        "application.yaml", "DEFAULT_GROUP", timeout=5.0
    )
    assert extension.normalize_instance({"ip": "", "port": 1}) is None


@pytest.mark.anyio
async def test_sync_sdk_work_does_not_block_event_loop(
    make_app, patched_create_client, fake_client
):
    app, config = make_app()
    extension = FastAPINacos(app, config)
    entered = threading.Event()
    release = threading.Event()

    def blocking_list(*_args, **_kwargs):
        entered.set()
        release.wait(1)
        return {"hosts": []}

    fake_client.list_naming_instance.side_effect = blocking_list
    task = asyncio.create_task(extension.list_instances(app, "orders"))
    loop = asyncio.get_running_loop()
    assert await loop.run_in_executor(None, entered.wait, 1)
    progressed = False
    await asyncio.sleep(0)
    progressed = True
    release.set()
    assert await task == []
    assert progressed is True


@pytest.mark.anyio
async def test_concurrent_lazy_client_is_created_once(make_app, patched_create_client, fake_client):
    app, config = make_app()
    extension = FastAPINacos(app, config)
    clients = await asyncio.gather(*(extension.get_client(app) for _ in range(20)))
    assert all(client is fake_client for client in clients)
    assert patched_create_client["count"] == 1


def test_health_route_openapi_conflict_and_contract(make_app, patched_create_client):
    app, config = make_app({"NACOS_HEALTH_CHECK_ENABLED": True})
    extension = FastAPINacos(app, config)
    client = TestClient(app)
    response = client.get("/health/nacos")
    assert response.status_code == 200
    assert set(response.json()) == {
        "status",
        "enabled",
        "client_created",
        "target_registered",
        "registered",
        "operation_running",
        "last_error",
    }
    assert response.json()["status"] == "ok"
    operation = client.get("/openapi.json").json()["paths"]["/health/nacos"]["get"]
    assert operation["operationId"].startswith(HEALTH_ENDPOINT)
    extension.init_app(app, config)
    assert sum(route.name == HEALTH_ENDPOINT for route in app.routes) == 1

    conflict = FastAPI()

    @conflict.get("/health/nacos")
    async def existing():
        return {"owner": "application"}

    conflict_extension = FastAPINacos(
        conflict,
        dict(config, NACOS_HEALTH_CHECK_ENABLED=True),
    )
    assert TestClient(conflict).get("/health/nacos").json() == {
        "owner": "application"
    }
    assert conflict_extension.get_status(conflict)["enabled"] is True


def test_health_route_reports_disabled_without_network(make_app, patched_create_client):
    app, config = make_app(
        {"NACOS_ENABLED": False, "NACOS_HEALTH_CHECK_ENABLED": True}
    )
    FastAPINacos(app, config)
    payload = TestClient(app).get("/health/nacos").json()
    assert payload["status"] == "disabled"
    assert payload["enabled"] is False
    assert payload["client_created"] is False
    assert patched_create_client["count"] == 0


def test_user_lifespan_is_composed_and_shutdown_deregisters(
    make_app, patched_create_client, fake_client
):
    events = []

    @asynccontextmanager
    async def user_lifespan(_app):
        events.append("user-start")
        yield
        events.append("user-stop")

    app, config = make_app(
        {"NACOS_AUTO_REGISTER": True, "NACOS_DEREGISTER_ON_EXIT": True},
        lifespan=user_lifespan,
    )
    extension = FastAPINacos(app, config)
    with TestClient(app):
        wait_registered(extension, app)
        events.append("request-window")
        assert extension.get_status(app)["registered"] is True

    assert events == ["user-start", "request-window", "user-stop"]
    fake_client.add_naming_instance.assert_called_once()
    fake_client.remove_naming_instance.assert_called_once()


def test_shutdown_honors_deregister_disabled(make_app, patched_create_client, fake_client):
    app, config = make_app(
        {"NACOS_AUTO_REGISTER": True, "NACOS_DEREGISTER_ON_EXIT": False}
    )
    extension = FastAPINacos(app, config)
    with TestClient(app):
        wait_registered(extension, app)
    fake_client.remove_naming_instance.assert_not_called()


def test_auto_registration_validation_is_eager_but_manual_is_deferred(make_app):
    auto_app, auto_config = make_app(
        {"NACOS_AUTO_REGISTER": True, "NACOS_SERVICE_NAME": None}
    )
    with pytest.raises(NacosValidationError, match="SERVICE_NAME"):
        FastAPINacos(auto_app, auto_config)

    manual_app, manual_config = make_app(
        {"NACOS_AUTO_REGISTER": False, "NACOS_SERVICE_NAME": None}
    )
    extension = FastAPINacos(manual_app, manual_config)
    with pytest.raises(NacosValidationError, match="SERVICE_NAME"):
        asyncio.run(extension.register_instance(manual_app))


def test_registration_failure_is_reported_locally(
    make_app, patched_create_client, fake_client
):
    fake_client.add_naming_instance.return_value = False
    app, config = make_app(
        {
            "NACOS_AUTO_REGISTER": True,
            "NACOS_RETRY_ENABLED": False,
            "NACOS_HEALTH_CHECK_ENABLED": True,
        }
    )
    extension = FastAPINacos(app, config)
    with TestClient(app) as client:
        wait_until(lambda: not extension.get_status(app)["operation_running"])
        status = extension.get_status(app)
        assert status["target_registered"] is True
        assert status["registered"] is False
        assert status["last_error"] == "NacosRegistrationError"
        assert client.get("/health/nacos").json()["status"] == "error"


def test_multi_application_state_is_isolated(make_app, patched_create_client):
    extension = FastAPINacos(config={"NACOS_SERVICE_PORT": 9000})
    app_a, config_a = make_app({"NACOS_SERVICE_NAME": "a"})
    app_b, config_b = make_app({"NACOS_SERVICE_NAME": "b", "NACOS_SERVICE_PORT": 9001})
    extension.init_app(app_a, config_a)
    extension.init_app(app_b, config_b)

    assert app_a.state.nacos is not app_b.state.nacos
    assert extension.get_config_snapshot(app_a)["NACOS_SERVICE_PORT"] == 8000
    assert extension.get_config_snapshot(app_b)["NACOS_SERVICE_PORT"] == 9001
