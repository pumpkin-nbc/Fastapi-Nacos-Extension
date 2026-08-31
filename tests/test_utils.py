"""Exhaustive tests for coercion, validation, IP detection and masking."""

from unittest.mock import MagicMock

import pytest

from fastapi_nacos import NacosValidationError, utils


@pytest.mark.parametrize(
    "value, default, expected",
    [
        (None, True, True),
        (True, False, True),
        (False, True, False),
        (1, False, True),
        (0.0, True, False),
        (" YES ", False, True),
        ("off", True, False),
        ("unknown", True, True),
        (object(), False, False),
    ],
)
def test_to_bool(value, default, expected):
    assert utils.to_bool(value, default) is expected


@pytest.mark.parametrize(
    "value, default, expected",
    [
        (None, 4, 4),
        (True, 4, 4),
        (2.0, None, 2),
        (2.5, 4, 4),
        (float("inf"), 4, 4),
        ("3", None, 3),
        ("bad", 4, 4),
    ],
)
def test_to_int(value, default, expected):
    assert utils.to_int(value, default) == expected


@pytest.mark.parametrize(
    "value, default, expected",
    [(None, 4.0, 4.0), (True, 4.0, 4.0), ("2.5", None, 2.5), ("bad", 4.0, 4.0)],
)
def test_to_float(value, default, expected):
    assert utils.to_float(value, default) == expected


def test_is_bool_and_metadata_and_masking():
    assert utils.is_bool(True)
    assert not utils.is_bool(1)
    assert utils.validate_metadata(None) == {}
    source = {"x": 1}
    assert utils.validate_metadata(source) == source
    assert utils.validate_metadata(source) is not source
    with pytest.raises(NacosValidationError, match="dict"):
        utils.validate_metadata([])
    masked = utils.mask_sensitive(
        {
            "NACOS_PASSWORD": "password",
            "NACOS_ACCESS_KEY": "access",
            "NACOS_SECRET_KEY": "secret",
            "NACOS_USERNAME": "visible",
            "NACOS_PASSWORD_EMPTY": "visible",
        }
    )
    assert masked == {
        "NACOS_PASSWORD": "***",
        "NACOS_ACCESS_KEY": "***",
        "NACOS_SECRET_KEY": "***",
        "NACOS_USERNAME": "visible",
        "NACOS_PASSWORD_EMPTY": "visible",
    }


@pytest.mark.parametrize(
    "validator, valid, invalid",
    [
        (utils.validate_port, [1, 65535, "8080", 80.0], [True, 0, 65536, 2.5, float("inf"), "bad"]),
        (utils.validate_weight, [0.1, "2"], [True, 0, -1, float("nan"), "bad"]),
        (utils.validate_heartbeat_interval, [0.1, "2"], [True, 0, -1, float("inf"), "bad"]),
        (utils.validate_retry_times, [1, "2", 3.0], [True, 0, 1.5, float("nan"), "bad"]),
        (utils.validate_retry_interval, [0, "2"], [True, -1, float("inf"), "bad"]),
        (utils.validate_request_timeout, [0.1, "2"], [True, 0, -1, float("nan"), "bad"]),
    ],
)
def test_numeric_validators(validator, valid, invalid):
    for value in valid:
        assert isinstance(validator(value), (int, float))
    for value in invalid:
        with pytest.raises(NacosValidationError):
            validator(value)


def test_local_ip_primary_fallback_and_failure(monkeypatch):
    primary = MagicMock()
    primary.getsockname.return_value = ("10.0.0.8", 1234)
    monkeypatch.setattr(utils.socket, "socket", MagicMock(return_value=primary))
    assert utils.get_local_ip() == "10.0.0.8"
    primary.close.assert_called_once()

    fallback = MagicMock()
    fallback.connect.side_effect = OSError
    monkeypatch.setattr(utils.socket, "socket", MagicMock(return_value=fallback))
    monkeypatch.setattr(utils.socket, "gethostname", lambda: "host")
    monkeypatch.setattr(utils.socket, "gethostbyname", lambda _host: "10.0.0.9")
    assert utils.get_local_ip() == "10.0.0.9"

    failed = MagicMock()
    failed.connect.side_effect = OSError
    monkeypatch.setattr(utils.socket, "socket", MagicMock(return_value=failed))
    monkeypatch.setattr(utils.socket, "gethostbyname", MagicMock(side_effect=OSError))
    assert utils.get_local_ip() is None
    assert utils.get_host_ip() == "127.0.0.1"
    with pytest.raises(NacosValidationError, match="auto-detect"):
        utils.get_local_ip(raise_on_failure=True)

