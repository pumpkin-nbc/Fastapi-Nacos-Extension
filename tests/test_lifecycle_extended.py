"""Failure recovery, concurrency, exit and fork lifecycle branches."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from types import SimpleNamespace

import pytest

import fastapi_nacos_extension.extension as extension_module
from fastapi_nacos_extension import FastAPINacos, NacosValidationError
from fastapi_nacos_extension._recovery import _LifecycleFailureStage
from tests.helpers import wait_registered, wait_until


def run_together(count, operation):
    barrier = Barrier(count)

    def invoke():
        barrier.wait()
        return operation()

    with ThreadPoolExecutor(max_workers=count) as executor:
        return list(executor.map(lambda _index: invoke(), range(count)))


def test_concurrent_registration_and_deregistration_share_single_rpc(
    make_app, patched_create_client, fake_client
):
    fake_client.add_naming_instance.side_effect = lambda *_a, **_k: (
        time.sleep(0.02) or True
    )
    app, config = make_app()
    extension = FastAPINacos(app, config)
    assert run_together(20, lambda: asyncio.run(extension.register_instance(app))) == [
        None
    ] * 20
    wait_registered(extension, app)
    assert fake_client.add_naming_instance.call_count == 1

    fake_client.remove_naming_instance.side_effect = lambda *_a, **_k: (
        time.sleep(0.02) or True
    )
    assert run_together(20, lambda: asyncio.run(extension.deregister_instance(app))) == [
        True
    ] * 20
    assert fake_client.remove_naming_instance.call_count == 1


def test_transient_worker_failure_enters_low_frequency_recovery(
    make_app, patched_create_client, fake_client, monkeypatch
):
    fake_client.add_naming_instance.side_effect = [
        ConnectionRefusedError("private"),
        ConnectionResetError("private"),
        True,
    ]
    rounds = []
    monkeypatch.setattr(
        FastAPINacos,
        "_lifecycle_recovery_delay",
        staticmethod(lambda _interval, round_number: rounds.append(round_number) or 0),
    )
    app, config = make_app(
        {"NACOS_RETRY_TIMES": 1, "NACOS_RETRY_INTERVAL": 0}
    )
    extension = FastAPINacos(app, config)
    asyncio.run(extension.register_instance(app))
    wait_registered(extension, app, timeout=3)
    assert fake_client.add_naming_instance.call_count == 3
    assert rounds[:2] == [1, 2]
    assert extension.get_status(app)["last_error"] is None


@pytest.mark.parametrize("final_failure", [False, NacosValidationError("bad")])
def test_recovery_stops_on_non_transient_failure(
    make_app, patched_create_client, fake_client, monkeypatch, final_failure
):
    fake_client.add_naming_instance.side_effect = [
        ConnectionRefusedError("private"),
        final_failure,
    ]
    monkeypatch.setattr(
        FastAPINacos,
        "_lifecycle_recovery_delay",
        staticmethod(lambda *_args: 0),
    )
    app, config = make_app(
        {"NACOS_RETRY_TIMES": 1, "NACOS_RETRY_INTERVAL": 0}
    )
    extension = FastAPINacos(app, config)
    asyncio.run(extension.register_instance(app))
    wait_until(lambda: not extension.get_status(app)["operation_running"])
    assert fake_client.add_naming_instance.call_count == 2
    assert extension.get_status(app)["registered"] is False


def test_client_creation_transient_failures_are_recovered(
    make_app, fake_client, monkeypatch
):
    outcomes = [ConnectionRefusedError(), ConnectionResetError(), fake_client]
    attempts = []

    def create(_config):
        attempts.append(True)
        outcome = outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr(extension_module, "create_client", create)
    monkeypatch.setattr(
        FastAPINacos,
        "_lifecycle_recovery_delay",
        staticmethod(lambda *_args: 0),
    )
    app, config = make_app(
        {"NACOS_RETRY_TIMES": 1, "NACOS_RETRY_INTERVAL": 0}
    )
    extension = FastAPINacos(app, config)
    asyncio.run(extension.register_instance(app))
    wait_registered(extension, app, timeout=3)
    assert len(attempts) == 3
    assert fake_client.add_naming_instance.call_count == 1
    assert app.state.nacos["_runtime"].naming_rpc_seq == 1


def test_shutdown_interrupts_recovery_wait(
    make_app, patched_create_client, fake_client
):
    fake_client.add_naming_instance.side_effect = ConnectionRefusedError("private")
    app, config = make_app(
        {
            "NACOS_RETRY_TIMES": 1,
            "NACOS_RETRY_INTERVAL": 100,
            "NACOS_DEREGISTER_ON_EXIT": False,
        }
    )
    extension = FastAPINacos(app, config)
    asyncio.run(extension.register_instance(app))
    wait_until(lambda: fake_client.add_naming_instance.call_count == 1)
    extension._atexit_handler(app)
    wait_until(lambda: not extension.get_status(app)["operation_running"])
    assert fake_client.add_naming_instance.call_count == 1


def test_naming_outcome_distinguishes_failure_and_skip(
    make_app, patched_create_client, fake_client
):
    app, config = make_app()
    extension = FastAPINacos(app, config)
    state = app.state.nacos
    runtime = state["_runtime"]
    identity = {
        "service_name": "test-service",
        "ip": "127.0.0.1",
        "port": 8000,
        "cluster_name": "DEFAULT",
        "group_name": "DEFAULT_GROUP",
        "ephemeral": True,
    }
    runtime.target_registered = True
    fake_client.add_naming_instance.return_value = False
    failed = extension._execute_naming_rpc(
        state,
        runtime,
        "register",
        fake_client,
        identity=identity,
        allow_during_shutdown=False,
        record_lifecycle_error=True,
        stage=_LifecycleFailureStage.REGISTER_RPC,
    )
    assert failed.result is extension_module._NamingResult.FAILED
    assert failed.rpc_executed is True
    assert runtime.last_error == "NacosRegistrationError"

    runtime.target_registered = False
    skipped = extension._execute_naming_rpc(
        state,
        runtime,
        "register",
        fake_client,
        identity=identity,
        allow_during_shutdown=False,
        record_lifecycle_error=True,
    )
    assert skipped.result is extension_module._NamingResult.SKIPPED
    assert skipped.rpc_executed is False


def test_atexit_registration_callback_and_missing_state_are_safe(
    make_app, patched_create_client, fake_client, monkeypatch
):
    callbacks = []
    monkeypatch.setattr(
        extension_module,
        "atexit",
        SimpleNamespace(register=lambda callback: callbacks.append(callback)),
    )
    app, config = make_app({"NACOS_DEREGISTER_ON_EXIT": True})
    extension = FastAPINacos(app, config)
    assert len(callbacks) == 1
    asyncio.run(extension.register_instance(app))
    wait_registered(extension, app)
    callbacks[0]()
    fake_client.remove_naming_instance.assert_called_once()
    delattr(app.state, "nacos")
    callbacks[0]()


def test_fork_hook_marks_state_stale_and_rebuilds_current_runtime(
    make_app, patched_create_client, monkeypatch
):
    callbacks = []
    monkeypatch.setattr(
        extension_module.os,
        "register_at_fork",
        lambda **kwargs: callbacks.append(kwargs["after_in_child"]),
        raising=False,
    )
    app, config = make_app()
    extension = FastAPINacos(app, config)
    old_runtime = app.state.nacos["_runtime"]
    callbacks[0]()
    assert app.state.nacos["_runtime_stale"] is True
    extension.get_status(app)
    assert app.state.nacos["_runtime"] is not old_runtime


def test_status_is_available_during_blocked_rpc(
    make_app, patched_create_client, fake_client
):
    entered = Event()
    release = Event()

    def block(*_args, **_kwargs):
        entered.set()
        release.wait(1)
        return True

    fake_client.add_naming_instance.side_effect = block
    app, config = make_app()
    extension = FastAPINacos(app, config)
    asyncio.run(extension.register_instance(app))
    assert entered.wait(1)
    status = extension.get_status(app)
    assert status["operation_running"] is True
    assert status["target_registered"] is True
    assert status["registered"] is False
    release.set()
    wait_registered(extension, app)
