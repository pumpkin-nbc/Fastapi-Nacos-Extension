"""Defensive and throttling branches of heartbeat instrumentation."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import fastapi_nacos.client as client_module


@pytest.mark.parametrize(
    "args, kwargs",
    [
        ((), {}),
        (("orders", "10.0.0.1"), {}),
        (("orders", "10.0.0.1", 80, None, 1, {}, True, "G", "extra"), {}),
        (("orders", "10.0.0.1", 80), {"unknown": True}),
        (("", "10.0.0.1", 80), {}),
        (("orders", "", 80), {}),
        (("orders", "10.0.0.1", 70000), {}),
        (("orders", "10.0.0.1", 80), {"group_name": None}),
        (("orders", "10.0.0.1", 80), {"cluster_name": ""}),
    ],
)
def test_heartbeat_identity_rejects_invalid_layout(args, kwargs):
    assert client_module._extract_heartbeat_identity(args, kwargs) is None


def test_failure_throttling_type_change_and_recovery(monkeypatch):
    original = MagicMock(
        side_effect=[
            RuntimeError("private-1"),
            RuntimeError("private-2"),
            ValueError("private-3"),
            {"ok": True},
            {"ok": True},
        ]
    )
    client = SimpleNamespace(send_heartbeat=original)
    safe_logger = MagicMock()
    moments = iter(float(value) for value in range(20))
    monkeypatch.setattr(client_module.time, "monotonic", lambda: next(moments))
    monkeypatch.setattr(client_module, "logger", safe_logger)
    client_module._install_heartbeat_logging(client)
    args = ("orders", "10.0.0.1", 80)
    for error_type in (RuntimeError, RuntimeError, ValueError):
        with pytest.raises(error_type):
            client.send_heartbeat(*args)
    assert client.send_heartbeat(*args) == {"ok": True}
    assert client.send_heartbeat(*args) == {"ok": True}
    assert safe_logger.warning.call_count == 2
    assert safe_logger.debug.call_count == 2
    assert safe_logger.info.call_count == 1
    assert "private" not in str(safe_logger.mock_calls)


def test_observer_and_logger_failures_do_not_change_sdk_contract(monkeypatch):
    original = MagicMock(return_value="sdk-result")
    client = SimpleNamespace(send_heartbeat=original)
    safe_logger = MagicMock()
    safe_logger.debug.side_effect = RuntimeError("logger-private")
    monkeypatch.setattr(client_module, "logger", safe_logger)

    def broken_observer(*_event):
        raise RuntimeError("observer-private")

    assert client_module._set_heartbeat_observer(client, broken_observer)
    assert client.send_heartbeat("orders", "10.0.0.1", 80) == "sdk-result"


def test_broken_clocks_skip_observer_but_preserve_sdk_result(monkeypatch):
    original = MagicMock(return_value=True)
    client = SimpleNamespace(send_heartbeat=original)
    observer = MagicMock()
    monkeypatch.setattr(
        client_module.time,
        "monotonic",
        MagicMock(side_effect=RuntimeError("clock-private")),
    )
    monkeypatch.setattr(
        client_module.time,
        "time",
        MagicMock(side_effect=RuntimeError("clock-private")),
    )
    assert client_module._set_heartbeat_observer(client, observer)
    assert client.send_heartbeat("orders", "10.0.0.1", 80) is True
    observer.assert_not_called()


def test_read_only_client_remains_usable_when_installation_fails(monkeypatch):
    class ReadOnlyClient:
        __slots__ = ()

        def send_heartbeat(self, *_args, **_kwargs):
            return "original"

    safe_logger = MagicMock()
    monkeypatch.setattr(client_module, "logger", safe_logger)
    client = ReadOnlyClient()
    assert client_module._install_heartbeat_instrumentation(client) is None
    assert client.send_heartbeat("orders", "10.0.0.1", 80) == "original"
    safe_logger.warning.assert_called_once()


def test_client_without_heartbeat_is_supported():
    client = object()
    assert client_module._install_heartbeat_instrumentation(client) is None
    assert client_module._set_heartbeat_observer(client, None) is False

