"""Small deterministic tests for private lifecycle decision helpers."""

from threading import current_thread
from unittest.mock import MagicMock

import pytest

import fastapi_nacos_extension.extension as extension_module
from fastapi_nacos_extension import FastAPINacos, NacosValidationError
from fastapi_nacos_extension._recovery import (
    _LifecycleFailure,
    _LifecycleFailureClass,
    _LifecycleFailureStage,
)


def runtime_for_worker():
    runtime = extension_module._AppRuntimeState()
    worker = current_thread()
    runtime.operation_kind = "register"
    runtime.operation_thread = worker
    runtime.target_registered = True
    return runtime, worker


@pytest.mark.parametrize(
    "failure_class,retry_enabled,max_attempts,recovery_round,real_attempt,expected",
    [
        (_LifecycleFailureClass.DETERMINISTIC, True, 3, 0, False, ("stop", 1, 0)),
        (_LifecycleFailureClass.UNKNOWN, False, 3, 0, False, ("stop", 1, 0)),
        (_LifecycleFailureClass.UNKNOWN, True, 3, 0, False, ("finite_wait", 1, 0)),
        (_LifecycleFailureClass.UNKNOWN, True, 1, 0, False, ("stop", 1, 0)),
        (_LifecycleFailureClass.TRANSIENT, True, 1, 0, False, ("recovery", 1, 1)),
        (_LifecycleFailureClass.TRANSIENT, True, 1, 1, True, ("recovery", 0, 2)),
        (_LifecycleFailureClass.TRANSIENT, True, 1, 1, False, ("recovery", 0, 1)),
        (_LifecycleFailureClass.UNKNOWN, True, 1, 1, True, ("stop", 0, 1)),
    ],
)
def test_worker_failure_decision_table(
    failure_class,
    retry_enabled,
    max_attempts,
    recovery_round,
    real_attempt,
    expected,
):
    extension = FastAPINacos()
    runtime, worker = runtime_for_worker()
    result = extension._handle_worker_failure(
        runtime,
        worker,
        "register",
        _LifecycleFailure(failure_class, "SafeFailure"),
        finite_attempts=0,
        recovery_round=recovery_round,
        retry_enabled=retry_enabled,
        max_attempts=max_attempts,
        real_recovery_attempt=real_attempt,
        log_state=extension_module._WorkerLogState(direction="register"),
    )
    assert result == expected


def test_worker_failure_stops_or_reevaluates_when_authority_changes():
    extension = FastAPINacos()
    failure = _LifecycleFailure(_LifecycleFailureClass.TRANSIENT, "Failure")
    runtime, worker = runtime_for_worker()
    runtime.operation_thread = object()
    assert extension._handle_worker_failure(
        runtime,
        worker,
        "register",
        failure,
        finite_attempts=1,
        recovery_round=0,
        retry_enabled=True,
        max_attempts=3,
        real_recovery_attempt=False,
        log_state=extension_module._WorkerLogState(),
    )[0] == "stop"

    runtime, worker = runtime_for_worker()
    runtime.target_registered = False
    runtime.registered = True
    assert extension._handle_worker_failure(
        runtime,
        worker,
        "register",
        failure,
        finite_attempts=1,
        recovery_round=0,
        retry_enabled=True,
        max_attempts=3,
        real_recovery_attempt=False,
        log_state=extension_module._WorkerLogState(),
    )[0] == "reevaluate"


def test_recovery_delay_wait_and_log_helpers(monkeypatch):
    observed = []
    monkeypatch.setattr(
        extension_module.random,
        "uniform",
        lambda lower, upper: observed.append((lower, upper)) or lower,
    )
    assert FastAPINacos._lifecycle_recovery_delay(0, 1) == 1.6
    assert FastAPINacos._lifecycle_recovery_delay(60, 1) == 60
    assert observed == [(1.6, 2.0), (60, 72.0)]

    runtime, worker = runtime_for_worker()
    assert FastAPINacos._interruptible_retry_wait(runtime, worker, 0) is True
    runtime.shutting_down = True
    assert FastAPINacos._interruptible_retry_wait(runtime, worker, 0) is False

    warnings = MagicMock()
    debug = MagicMock()
    info = MagicMock()
    monkeypatch.setattr(extension_module.logger, "warning", warnings)
    monkeypatch.setattr(extension_module.logger, "debug", debug)
    monkeypatch.setattr(extension_module.logger, "info", info)
    state = extension_module._WorkerLogState(direction="register")
    failure = _LifecycleFailure(_LifecycleFailureClass.TRANSIENT, "Failure")
    FastAPINacos._log_worker_failure(
        "register", failure, state, entering_recovery=False
    )
    FastAPINacos._log_worker_failure(
        "register", failure, state, entering_recovery=False
    )
    assert warnings.call_count == 1
    assert debug.call_count == 1
    FastAPINacos._log_worker_recovered("register", state)
    state.recovery_active = True
    FastAPINacos._log_worker_recovered("register", state)
    info.assert_called_once()


def test_prepare_register_locked_decision_branches(make_app, monkeypatch):
    app, config = make_app()
    extension = FastAPINacos(app, config)
    state = app.state.nacos
    runtime = state["_runtime"]

    disabled_state = dict(state)
    disabled_state["config"] = dict(state["config"], NACOS_ENABLED=False)
    assert extension._prepare_register_locked(
        disabled_state, runtime, new_command=True
    ) == (None, None)
    runtime.shutting_down = True
    assert extension._prepare_register_locked(state, runtime, new_command=True) == (
        None,
        None,
    )
    runtime.shutting_down = False
    runtime.registered = True
    assert extension._prepare_register_locked(state, runtime, new_command=True) == (
        None,
        None,
    )
    runtime.registered = False
    runtime.operation_kind = "register"
    assert extension._prepare_register_locked(state, runtime, new_command=True) == (
        None,
        None,
    )

    runtime.operation_kind = None
    error = NacosValidationError("invalid")
    state["_registration_config_error"] = error
    thread, returned = extension._prepare_register_locked(
        state, runtime, new_command=True
    )
    assert thread is None and returned is error

    state["_registration_config_error"] = None
    monkeypatch.setattr(
        extension_module,
        "Thread",
        MagicMock(side_effect=RuntimeError("thread-private")),
    )
    thread, returned = extension._prepare_register_locked(
        state, runtime, new_command=True
    )
    assert thread is None and returned is None
    assert runtime.last_error == "ThreadCreateError"


def test_thread_start_failure_is_committed(make_app):
    app, config = make_app()
    extension = FastAPINacos(app, config)
    runtime = app.state.nacos["_runtime"]
    thread = MagicMock()
    thread.start.side_effect = RuntimeError("private")
    runtime.target_registered = True
    runtime.operation_kind = "register"
    runtime.operation_thread = thread
    extension._start_registration_thread(app, app.state.nacos, runtime, thread)
    assert runtime.operation_kind is None
    assert runtime.operation_thread is None
    assert runtime.last_error == "ThreadStartError"


@pytest.mark.parametrize(
    "value, expected",
    [
        (3, 3.0),
        (True, None),
        ("3", None),
        (0, None),
        (float("nan"), None),
    ],
)
def test_naming_timeout_validation(value, expected):
    client = MagicMock()
    client.default_timeout = value
    assert FastAPINacos._naming_timeout_seconds(client) == expected


def test_naming_stage_gate_and_error_helpers():
    assert FastAPINacos._default_naming_stage(
        "register", False
    ) is _LifecycleFailureStage.REGISTER_RPC
    assert FastAPINacos._default_naming_stage(
        "deregister", True
    ) is _LifecycleFailureStage.EXIT_DEREGISTER_RPC
    assert FastAPINacos._default_naming_stage(
        "deregister", False
    ) is _LifecycleFailureStage.SYNC_DEREGISTER_RPC

    runtime = extension_module._AppRuntimeState()
    runtime.target_registered = True
    assert FastAPINacos._naming_rpc_gate_locked(
        runtime, "register", False
    ) is extension_module._NamingResult.FAILED
    assert FastAPINacos._naming_rpc_gate_locked(
        runtime, "unknown", False
    ) is extension_module._NamingResult.SKIPPED
    FastAPINacos._record_rpc_error_locked(runtime, "register", "Failure")
    assert runtime.last_error == "Failure"
    runtime.registered = True
    FastAPINacos._record_rpc_error_locked(runtime, "register", "ignored")
    assert runtime.last_error is None


def test_heartbeat_identity_and_time_helpers(monkeypatch):
    assert FastAPINacos._heartbeat_time_value(1) == 1.0
    assert FastAPINacos._heartbeat_time_value(True) is None
    assert FastAPINacos._heartbeat_time_value(float("inf")) is None
    assert FastAPINacos._heartbeat_time_value("1") is None

    valid = ("svc", "DEFAULT_GROUP", "DEFAULT", "10.0.0.1", 80)
    registered = {
        "service_name": "svc",
        "group_name": None,
        "cluster_name": None,
        "ip": "10.0.0.1",
        "port": 80,
    }
    assert FastAPINacos._heartbeat_identity_matches_registered(valid, registered)
    assert not FastAPINacos._heartbeat_identity_matches_registered(None, registered)
    for invalid in [
        (None, None, None, "ip", 80),
        ("svc", "", None, "ip", 80),
        ("svc", None, "", "ip", 80),
        ("svc", None, None, "", 80),
        ("svc", None, None, "ip", True),
        ("svc", None, None, "ip", 0),
    ]:
        assert FastAPINacos._normalize_heartbeat_instance_identity(*invalid) is None

    runtime = extension_module._AppRuntimeState()
    monkeypatch.setattr(extension_module.time, "monotonic", lambda: 10.0)
    FastAPINacos._start_heartbeat_observation_locked(runtime, {"ephemeral": True})
    assert runtime.heartbeat_state == "unknown"
    assert runtime.heartbeat_cycle_started_monotonic == 10.0
    FastAPINacos._clear_heartbeat_observation_locked(runtime)
    assert runtime.heartbeat_state == "not_applicable"
    assert runtime.heartbeat_cycle_started_monotonic is None
