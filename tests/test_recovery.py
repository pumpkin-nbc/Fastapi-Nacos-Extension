"""Structured lifecycle failure classification tests."""

import errno
import socket
from types import SimpleNamespace
from unittest.mock import MagicMock

import nacos.exception
import pytest

import fastapi_nacos._recovery as recovery_module
from fastapi_nacos import NacosConfigError
from fastapi_nacos._recovery import (
    _classify_lifecycle_failure,
    _LifecycleFailureClass,
    _LifecycleFailureStage,
    _synthetic_lifecycle_failure,
)


def classify(error, stage=_LifecycleFailureStage.REGISTER_RPC, direction="register"):
    return _classify_lifecycle_failure(error, stage=stage, direction=direction)


@pytest.mark.parametrize(
    "error",
    [
        NacosConfigError("bad"),
        ValueError("bad"),
        TypeError("bad"),
        ImportError("bad"),
        KeyError("bad"),
        AssertionError("bad"),
        PermissionError("bad"),
    ],
)
def test_deterministic_builtin_failures(error):
    result = classify(error)
    assert result.failure_class is _LifecycleFailureClass.DETERMINISTIC
    assert result.safe_error_type == type(error).__name__


@pytest.mark.parametrize(
    "error",
    [
        TimeoutError("late"),
        ConnectionError("offline"),
        OSError(errno.ECONNREFUSED, "refused"),
        OSError(errno.ETIMEDOUT, "timeout"),
        socket.gaierror(getattr(socket, "EAI_AGAIN", -3), "again"),
    ],
)
def test_transient_builtin_failures(error):
    assert classify(error).failure_class is _LifecycleFailureClass.TRANSIENT


@pytest.mark.parametrize("status", [408, 425, 429, 500, 502, 503, 504, "503"])
def test_transient_http_statuses(status):
    error = RuntimeError("private")
    error.response = SimpleNamespace(status_code=status)
    assert classify(error).failure_class is _LifecycleFailureClass.TRANSIENT


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422])
def test_deterministic_http_statuses_override_transient(status):
    error = ConnectionError("private")
    error.status_code = status
    assert classify(error).failure_class is _LifecycleFailureClass.DETERMINISTIC


@pytest.mark.parametrize(
    "code, expected",
    [
        ("service-unavailable", _LifecycleFailureClass.TRANSIENT),
        ("request_timeout", _LifecycleFailureClass.TRANSIENT),
        ("permission-denied", _LifecycleFailureClass.DETERMINISTIC),
        ("invalid_parameter", _LifecycleFailureClass.DETERMINISTIC),
        ("something-new", _LifecycleFailureClass.UNKNOWN),
    ],
)
def test_structured_error_codes(code, expected):
    error = RuntimeError("private")
    error.error_code = code
    assert classify(error).failure_class is expected


def test_exception_chain_and_cycles_are_safe():
    wrapper = RuntimeError("wrapper")
    wrapper.__cause__ = TimeoutError("private")
    assert classify(wrapper).failure_class is _LifecycleFailureClass.TRANSIENT

    first = RuntimeError("one")
    second = RuntimeError("two")
    first.__cause__ = second
    second.__cause__ = first
    assert classify(first).failure_class is _LifecycleFailureClass.UNKNOWN

    chain = [RuntimeError(str(index)) for index in range(20)]
    for current, following in zip(chain, chain[1:]):
        current.__cause__ = following
    assert classify(chain[0]).failure_class is _LifecycleFailureClass.UNKNOWN


def test_hostile_structured_attributes_cannot_escape_classifier():
    class HostileError(Exception):
        def __getattribute__(self, name):
            if name in {
                "errno",
                "status_code",
                "http_status",
                "http_status_code",
                "status",
                "code",
                "response",
                "error_code",
                "__cause__",
                "__context__",
            }:
                raise RuntimeError("private")
            return super().__getattribute__(name)

    result = classify(HostileError("secret"))
    assert result.failure_class is _LifecycleFailureClass.UNKNOWN
    assert result.safe_error_type == "HostileError"


def test_synthetic_failure_is_sanitized():
    result = _synthetic_lifecycle_failure(
        "ClientUnavailable", _LifecycleFailureClass.DETERMINISTIC
    )
    assert result.failure_class is _LifecycleFailureClass.DETERMINISTIC
    assert result.safe_error_type == "ClientUnavailable"


def test_installed_bare_sdk_exception_uses_verified_version_surface(monkeypatch):
    error = nacos.exception.NacosRequestException()
    monkeypatch.setattr(recovery_module, "_installed_sdk_version", lambda: "2.0.11")
    result = classify(error)
    assert result.failure_class is _LifecycleFailureClass.TRANSIENT
    unverified = classify(
        error,
        stage=_LifecycleFailureStage.EXIT_DEREGISTER_RPC,
        direction="deregister",
    )
    assert unverified.failure_class is _LifecycleFailureClass.UNKNOWN


def test_sdk_introspection_helpers_fail_closed(monkeypatch):
    monkeypatch.setattr(
        recovery_module.importlib_metadata,
        "version",
        MagicMock(side_effect=RuntimeError("private")),
    )
    assert recovery_module._installed_sdk_version() is None
    monkeypatch.setattr(
        recovery_module.importlib,
        "import_module",
        MagicMock(side_effect=ImportError()),
    )
    assert recovery_module._installed_bare_request_exception_type() is None


def test_private_structured_parsers_are_conservative():
    assert recovery_module._structured_integer(True) is None
    assert recovery_module._structured_integer(12) == 12
    assert recovery_module._structured_integer(" 503 ") == 503
    assert recovery_module._structured_integer("5.0") is None
    assert recovery_module._normalized_error_code(None) is None
    assert recovery_module._normalized_error_code(" service-unavailable ") == (
        "SERVICE_UNAVAILABLE"
    )
    assert recovery_module._normalized_error_code(" ") is None
