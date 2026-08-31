"""Configuration, validation and isolation contracts."""

import pytest

from fastapi_nacos_extension import FastAPINacos, NacosConfigError, NacosValidationError
from fastapi_nacos_extension.config import (
    DEFAULTS,
    load_config,
    validate_connection_config,
    validate_registration_config,
)


def test_defaults_and_precedence(make_app):
    app, app_config = make_app(
        {"NACOS_SERVER_ADDR": "app:8848", "NACOS_SERVICE_METADATA": {"a": 1}}
    )
    extension = FastAPINacos(
        config={"NACOS_SERVER_ADDR": "constructor:8848", "NACOS_RETRY_TIMES": "4"}
    )
    extension.init_app(app, app_config)
    snapshot = extension.get_config_snapshot(app)

    assert snapshot["NACOS_SERVER_ADDR"] == "app:8848"
    assert snapshot["NACOS_RETRY_TIMES"] == 4
    assert snapshot["NACOS_LOG_FILENAME"] == "fastapi-nacos-extension.log"
    assert set(DEFAULTS).issubset(snapshot)


def test_configuration_is_snapshotted_per_app(make_app):
    source = {"NACOS_SERVICE_METADATA": {"version": "one"}}
    app_a, config_a = make_app(source)
    app_b, config_b = make_app({"NACOS_SERVICE_NAME": "service-b"})
    extension = FastAPINacos()
    extension.init_app(app_a, config_a)
    extension.init_app(app_b, config_b)
    source["NACOS_SERVICE_METADATA"]["version"] = "changed"

    assert extension.get_config_snapshot(app_a)["NACOS_SERVICE_METADATA"] == {
        "version": "one"
    }
    assert extension.get_config_snapshot(app_b)["NACOS_SERVICE_NAME"] == "service-b"

    returned = extension.get_config_snapshot(app_a)
    returned["NACOS_SERVICE_METADATA"]["version"] = "caller-change"
    assert extension.get_config_snapshot(app_a)["NACOS_SERVICE_METADATA"] == {
        "version": "one"
    }


def test_constructor_rejects_non_mapping_config():
    with pytest.raises(NacosConfigError, match="mapping"):
        FastAPINacos(config=[])


@pytest.mark.parametrize("value", [None, [], "not-a-mapping"])
def test_load_config_rejects_non_mapping(value):
    if value is None:
        assert load_config(value)["NACOS_ENABLED"] is True
    else:
        with pytest.raises(NacosConfigError, match="mapping"):
            load_config(value)


@pytest.mark.parametrize(
    "config, message",
    [
        ({"NACOS_SERVER_ADDR": ""}, "SERVER_ADDR"),
        (
            {
                "NACOS_SERVER_ADDR": "localhost:8848",
                "NACOS_USERNAME": "user",
                "NACOS_PASSWORD": None,
            },
            "configured together",
        ),
        (
            {
                "NACOS_SERVER_ADDR": "localhost:8848",
                "NACOS_ACCESS_KEY": "key",
                "NACOS_SECRET_KEY": None,
            },
            "configured together",
        ),
    ],
)
def test_connection_validation(config, message):
    with pytest.raises(NacosConfigError, match=message):
        validate_connection_config(config)


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"NACOS_SERVICE_NAME": None}, "SERVICE_NAME"),
        ({"NACOS_SERVICE_PORT": None}, "SERVICE_PORT"),
        ({"NACOS_SERVICE_PORT": 0}, "range"),
        ({"NACOS_SERVICE_WEIGHT": -1}, "greater"),
        ({"NACOS_SERVICE_METADATA": []}, "dict"),
        ({"NACOS_SERVICE_EPHEMERAL": "true"}, "bool"),
        ({"NACOS_SERVICE_HEARTBEAT_INTERVAL": 0}, "greater"),
    ],
)
def test_registration_validation(overrides, message):
    config = load_config(
        {
            "NACOS_SERVICE_NAME": "service",
            "NACOS_SERVICE_IP": "127.0.0.1",
            "NACOS_SERVICE_PORT": 8000,
        },
        overrides,
    )
    with pytest.raises(NacosValidationError, match=message):
        validate_registration_config(config)
