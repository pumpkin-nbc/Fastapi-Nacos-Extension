"""Registration state machine, exact identity and PID rebuild tests."""

import asyncio
import threading

from fastapi_nacos import FastAPINacos
from tests.helpers import wait_registered


def test_register_deregister_and_idempotency(make_app, patched_create_client, fake_client):
    app, config = make_app()
    extension = FastAPINacos(app, config)

    asyncio.run(extension.register_instance(app))
    wait_registered(extension, app)
    asyncio.run(extension.register_instance(app))
    wait_registered(extension, app)
    assert fake_client.add_naming_instance.call_count == 1

    assert asyncio.run(extension.deregister_instance(app)) is True
    wait_registered(extension, app, expected=False)
    assert asyncio.run(extension.deregister_instance(app)) is True
    assert fake_client.remove_naming_instance.call_count == 1


def test_deregister_uses_cached_registration_identity(
    make_app, patched_create_client, fake_client
):
    app, config = make_app(
        {
            "NACOS_SERVICE_GROUP": "BLUE_GROUP",
            "NACOS_SERVICE_CLUSTER": "BLUE",
            "NACOS_SERVICE_EPHEMERAL": False,
        }
    )
    extension = FastAPINacos(app, config)
    asyncio.run(extension.register_instance(app))
    wait_registered(extension, app)

    state_config = app.state.nacos["config"]
    state_config.update(
        {
            "NACOS_SERVICE_NAME": "changed",
            "NACOS_SERVICE_IP": "10.0.0.9",
            "NACOS_SERVICE_PORT": 9999,
        }
    )
    assert asyncio.run(extension.deregister_instance(app)) is True
    fake_client.remove_naming_instance.assert_called_once_with(
        "test-service",
        "127.0.0.1",
        8000,
        cluster_name="BLUE",
        ephemeral=False,
        group_name="BLUE_GROUP",
    )


def test_last_command_wins_during_blocked_register(
    make_app, patched_create_client, fake_client
):
    entered = threading.Event()
    release = threading.Event()

    def blocked_register(*_args, **_kwargs):
        entered.set()
        release.wait(1)
        return True

    fake_client.add_naming_instance.side_effect = blocked_register
    app, config = make_app({"NACOS_RETRY_ENABLED": False})
    extension = FastAPINacos(app, config)
    asyncio.run(extension.register_instance(app))
    assert entered.wait(1)

    result = {}

    def deregister():
        result["value"] = asyncio.run(extension.deregister_instance(app))

    thread = threading.Thread(target=deregister)
    thread.start()
    release.set()
    thread.join(2)
    wait_registered(extension, app, expected=False)
    assert result["value"] is True
    assert fake_client.remove_naming_instance.call_count == 1


def test_transient_registration_failure_can_recover(
    make_app, patched_create_client, fake_client
):
    fake_client.add_naming_instance.side_effect = [OSError("offline"), True]
    app, config = make_app(
        {"NACOS_RETRY_ENABLED": True, "NACOS_RETRY_TIMES": 2}
    )
    extension = FastAPINacos(app, config)
    asyncio.run(extension.register_instance(app))
    wait_registered(extension, app)
    assert fake_client.add_naming_instance.call_count == 2
    assert extension.get_status(app)["last_error"] is None


def test_pid_change_rebuilds_runtime_and_client(
    make_app, patched_create_client, monkeypatch
):
    app, config = make_app()
    extension = FastAPINacos(app, config)
    first_client = asyncio.run(extension.get_client(app))
    old_runtime = app.state.nacos["_runtime"]
    old_pid = old_runtime.pid
    monkeypatch.setattr("fastapi_nacos.lifecycle.current_pid", lambda: old_pid + 1000)

    status = extension.get_status(app)
    assert status["pid"] == old_pid + 1000
    assert app.state.nacos["_runtime"] is not old_runtime
    assert extension.get_cached_client(app) is None
    assert asyncio.run(extension.get_client(app)) is first_client
    assert patched_create_client["count"] == 2


def test_heartbeat_observation_updates_only_current_registered_identity(
    make_app, patched_create_client, fake_client
):
    app, config = make_app()
    extension = FastAPINacos(app, config)
    asyncio.run(extension.register_instance(app))
    wait_registered(extension, app)
    runtime = app.state.nacos["_runtime"]
    observer = extension._make_heartbeat_observer(app, runtime)
    started = runtime.heartbeat_cycle_started_monotonic

    observer(
        ("test-service", "DEFAULT_GROUP", "DEFAULT", "127.0.0.1", 8000),
        False,
        started,
        started + 0.1,
        123.0,
        "ConnectionError",
    )
    status = extension.get_status(app)
    assert status["heartbeat_state"] == "failing"
    assert status["last_heartbeat_failure_at"] == 123.0
    assert status["heartbeat_error_type"] == "ConnectionError"

    observer(
        ("another", "DEFAULT_GROUP", "DEFAULT", "127.0.0.1", 8000),
        True,
        started,
        started + 0.2,
        124.0,
        None,
    )
    assert extension.get_status(app)["heartbeat_state"] == "failing"
