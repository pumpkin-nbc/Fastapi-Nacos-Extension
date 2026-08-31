"""SDK construction, heartbeat instrumentation and log safety."""

import logging
from unittest.mock import MagicMock

import nacos
import pytest

from fastapi_nacos import NacosClientError, NacosLoggingError
from fastapi_nacos.client import (
    _extract_heartbeat_identity,
    _install_heartbeat_instrumentation,
    _set_heartbeat_observer,
    create_client,
)
from fastapi_nacos.config import load_config
from fastapi_nacos.logging import (
    SDK_LOGGER_NAMES,
    configure_logger,
    get_log_level,
    validate_logging_config,
)


@pytest.mark.parametrize(
    "args, kwargs, expected",
    [
        (("svc", "10.0.0.1", 80), {}, ("svc", "DEFAULT_GROUP", None, "10.0.0.1", 80)),
        (
            (),
            {"service_name": "svc", "ip": "10.0.0.1", "port": 80, "cluster_name": "BLUE"},
            ("svc", "DEFAULT_GROUP", "BLUE", "10.0.0.1", 80),
        ),
        (("svc", "10.0.0.1", True), {}, None),
        (("svc", "10.0.0.1", 80), {"service_name": "duplicate"}, None),
    ],
)
def test_extract_heartbeat_identity(args, kwargs, expected):
    assert _extract_heartbeat_identity(args, kwargs) == expected


def test_heartbeat_instrumentation_preserves_result_exception_and_observes():
    client = MagicMock()
    client.send_heartbeat.return_value = "result"
    instrumentation = _install_heartbeat_instrumentation(client)
    assert instrumentation is not None
    assert _install_heartbeat_instrumentation(client) is instrumentation
    observations = []
    assert _set_heartbeat_observer(client, lambda *event: observations.append(event))

    assert client.send_heartbeat("svc", "10.0.0.1", 80) == "result"
    assert observations[-1][0] == ("svc", "DEFAULT_GROUP", None, "10.0.0.1", 80)
    assert observations[-1][1] is True

    instrumentation.original_send_heartbeat.side_effect = OSError("token=secret")
    with pytest.raises(OSError, match="token=secret"):
        client.send_heartbeat("svc", "10.0.0.1", 80)
    assert observations[-1][1] is False
    assert observations[-1][-1] == "OSError"


def test_create_client_classic_constructor(monkeypatch):
    constructed = []

    class FakeSDKClient:
        def __init__(self, server_addresses, **kwargs):
            constructed.append((server_addresses, kwargs))

        def send_heartbeat(self, *_args, **_kwargs):
            return True

    monkeypatch.setattr(nacos, "NacosClient", FakeSDKClient)
    config = load_config(
        {
            "NACOS_SERVER_ADDR": "nacos:8848",
            "NACOS_NAMESPACE_ID": "namespace",
            "NACOS_USERNAME": "user",
            "NACOS_PASSWORD": "password",
        }
    )
    client = create_client(config)
    assert isinstance(client, FakeSDKClient)
    assert constructed[0][0] == "nacos:8848"
    assert constructed[0][1]["namespace"] == "namespace"
    assert constructed[0][1]["username"] == "user"
    assert constructed[0][1]["password"] == "password"


def test_create_client_wraps_constructor_failure(monkeypatch):
    class BrokenClient:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("credentials=secret")

    monkeypatch.setattr(nacos, "NacosClient", BrokenClient)
    with pytest.raises(NacosClientError) as caught:
        create_client(load_config())
    assert "credentials=secret" not in str(caught.value)


@pytest.mark.parametrize("value", [None, "TRACE", 10])
def test_invalid_log_level(value):
    with pytest.raises(NacosLoggingError):
        get_log_level(value)


def test_logging_disabled_and_sdk_loggers_are_silenced():
    configure_logger(None, load_config({"NACOS_LOG_ENABLED": False}))
    package_logger = logging.getLogger("fastapi_nacos")
    assert package_logger.disabled is True
    for name in SDK_LOGGER_NAMES:
        sdk_logger = logging.getLogger(name)
        assert sdk_logger.disabled is True
        assert sdk_logger.propagate is False


def test_logging_validation_rejects_unsafe_filename():
    config = load_config(
        {
            "NACOS_LOG_ENABLED": True,
            "NACOS_LOG_FILE_ENABLED": True,
            "NACOS_LOG_FILENAME": "../secret.log",
        }
    )
    with pytest.raises(NacosLoggingError, match="filename"):
        validate_logging_config(config)
