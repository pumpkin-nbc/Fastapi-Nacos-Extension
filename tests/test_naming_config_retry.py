"""Low-level SDK adapter and retry error contracts."""

from unittest.mock import MagicMock

import pytest

from fastapi_nacos import (
    NacosConfigError,
    NacosDeregistrationError,
    NacosDiscoveryError,
    NacosRegistrationError,
    NacosValidationError,
)
from fastapi_nacos.config import load_config
from fastapi_nacos.config_center import get_config
from fastapi_nacos.naming import (
    deregister_instance,
    register_instance,
    resolve_instance_identity,
)
from fastapi_nacos.retry import run_with_retry


def registration_config(**overrides):
    config = load_config(
        {
            "NACOS_SERVICE_NAME": "orders",
            "NACOS_SERVICE_IP": "10.0.0.1",
            "NACOS_SERVICE_PORT": 8080,
        }
    )
    config.update(overrides)
    return config


def test_resolve_register_and_deregister_classic_sdk_surface():
    client = MagicMock()
    client.add_naming_instance.return_value = True
    client.remove_naming_instance.return_value = True
    config = registration_config(
        NACOS_SERVICE_CLUSTER="BLUE",
        NACOS_SERVICE_GROUP="GROUP",
        NACOS_SERVICE_METADATA={"version": "v1"},
        NACOS_SERVICE_HEARTBEAT_INTERVAL=3.0,
    )
    identity = resolve_instance_identity(config)
    assert identity == {
        "service_name": "orders",
        "ip": "10.0.0.1",
        "port": 8080,
        "cluster_name": "BLUE",
        "group_name": "GROUP",
        "ephemeral": True,
    }
    assert register_instance(client, config, identity) is True
    client.add_naming_instance.assert_called_once_with(
        "orders",
        "10.0.0.1",
        8080,
        cluster_name="BLUE",
        weight=1.0,
        metadata={"version": "v1"},
        enable=True,
        healthy=True,
        ephemeral=True,
        group_name="GROUP",
        heartbeat_interval=3.0,
    )
    assert deregister_instance(client, config, identity) is True


@pytest.mark.parametrize("operation", ["register", "deregister"])
@pytest.mark.parametrize("failure", [False, RuntimeError("sdk failure")])
def test_naming_failures_are_domain_errors(operation, failure):
    client = MagicMock()
    method = (
        client.add_naming_instance
        if operation == "register"
        else client.remove_naming_instance
    )
    if isinstance(failure, BaseException):
        method.side_effect = failure
    else:
        method.return_value = failure
    function = register_instance if operation == "register" else deregister_instance
    error = NacosRegistrationError if operation == "register" else NacosDeregistrationError
    with pytest.raises(error, match="Failed to"):
        function(client, registration_config())


def test_config_center_returns_raw_content_and_defaults():
    client = MagicMock()
    client.get_config.return_value = '{"feature": true}'
    config = load_config(
        {"NACOS_CONFIG_GROUP": "APP", "NACOS_REQUEST_TIMEOUT": "2.5"}
    )
    assert get_config(client, config, "settings.json") == '{"feature": true}'
    client.get_config.assert_called_once_with("settings.json", "APP", timeout=2.5)


def test_config_center_validation_and_sdk_failure():
    with pytest.raises(NacosValidationError, match="data_id"):
        get_config(MagicMock(), load_config(), None)
    with pytest.raises(NacosConfigError, match="not available"):
        get_config(None, load_config(), "id")
    client = MagicMock()
    client.get_config.side_effect = OSError("secret body")
    with pytest.raises(NacosConfigError, match="SDK get_config"):
        get_config(client, load_config(), "id")


def test_retry_success_exhaustion_disabled_and_validation(monkeypatch):
    attempts = []
    sleeps = []
    monkeypatch.setattr("fastapi_nacos.retry._sleep", sleeps.append)

    def eventually():
        attempts.append(1)
        if len(attempts) < 3:
            raise OSError("offline")
        return "ok"

    config = {
        "NACOS_RETRY_ENABLED": True,
        "NACOS_RETRY_TIMES": 3,
        "NACOS_RETRY_INTERVAL": 0.25,
    }
    assert run_with_retry(eventually, "operation", config) == "ok"
    assert len(attempts) == 3
    assert sleeps == [0.25, 0.25]

    error = RuntimeError("failed")
    with pytest.raises(RuntimeError) as caught:
        run_with_retry(
            MagicMock(side_effect=error),
            "operation",
            dict(config, NACOS_RETRY_TIMES=2),
        )
    assert caught.value is error

    once = MagicMock(return_value=1)
    assert run_with_retry(once, "operation", {"NACOS_RETRY_ENABLED": False}) == 1
    once.assert_called_once()

    deterministic = MagicMock(side_effect=NacosValidationError("bad"))
    with pytest.raises(NacosValidationError):
        run_with_retry(deterministic, "operation", config)
    deterministic.assert_called_once()


def test_discovery_sdk_exception_has_sanitized_contract():
    from fastapi_nacos.naming import list_instances

    client = MagicMock()
    client.list_naming_instance.side_effect = RuntimeError("token=secret")
    with pytest.raises(NacosDiscoveryError) as caught:
        list_instances(client, load_config(), "orders")
    assert "token=secret" not in str(caught.value)

