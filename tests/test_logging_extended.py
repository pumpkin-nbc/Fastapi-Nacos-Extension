"""Logging handler reconciliation, validation, rotation and isolation."""

import logging
from logging.handlers import RotatingFileHandler
from unittest.mock import MagicMock

import pytest

import fastapi_nacos_extension.logging as nlog
from fastapi_nacos_extension import NacosLoggingError
from fastapi_nacos_extension.config import load_config


@pytest.fixture(autouse=True)
def clean_managed_loggers():
    names = (nlog.FASTAPI_NACOS_LOGGER_NAME, *nlog.SDK_LOGGER_NAMES)
    snapshots = {}
    for name in names:
        logger = logging.getLogger(name)
        snapshots[name] = (list(logger.handlers), logger.level, logger.propagate, logger.disabled)
        logger.handlers.clear()
        logger.disabled = False
        logger.propagate = True
        logger.setLevel(logging.NOTSET)
    yield
    for name, (handlers, level, propagate, disabled) in snapshots.items():
        logger = logging.getLogger(name)
        for handler in list(logger.handlers):
            if handler not in handlers:
                handler.close()
        logger.handlers[:] = handlers
        logger.setLevel(level)
        logger.propagate = propagate
        logger.disabled = disabled


def config(**overrides):
    return load_config({"NACOS_LOG_ENABLED": True, **overrides})


def owned(logger, kind):
    return [
        handler
        for handler in logger.handlers
        if getattr(handler, "_fastapi_nacos_extension_handler_type", None) == kind
    ]


def test_console_configuration_is_colored_and_deduplicated(capsys):
    cfg = config(NACOS_LOG_FILE_ENABLED=False, NACOS_LOG_LEVEL="DEBUG")
    nlog.configure_logger(None, cfg)
    nlog.configure_logger(None, cfg)
    logger = logging.getLogger(nlog.FASTAPI_NACOS_LOGGER_NAME)
    assert len(owned(logger, "console")) == 1
    for level, message in [
        (logging.DEBUG, "debug"),
        (logging.INFO, "info"),
        (logging.WARNING, "warning"),
        (logging.ERROR, "error"),
        (logging.CRITICAL, "critical"),
    ]:
        logger.log(level, message)
    output = capsys.readouterr().err
    assert all(message in output for message in ("debug", "info", "warning", "error", "critical"))
    assert output.count("\033[0m") == 5


def test_file_configuration_rotation_plain_text_and_reconciliation(tmp_path):
    cfg = config(
        NACOS_LOG_CONSOLE_ENABLED=False,
        NACOS_LOG_PATH=str(tmp_path),
        NACOS_LOG_FILENAME="custom.log",
        NACOS_LOG_MAX_BYTES="1024",
        NACOS_LOG_BACKUP_COUNT="2",
    )
    nlog.configure_logger(None, cfg)
    logger = logging.getLogger(nlog.FASTAPI_NACOS_LOGGER_NAME)
    handlers = owned(logger, "file")
    assert len(handlers) == 1
    assert isinstance(handlers[0], RotatingFileHandler)
    logger.error("plain-record")
    handlers[0].flush()
    assert "plain-record" in (tmp_path / "custom.log").read_text(encoding="utf-8")
    assert "\033[" not in (tmp_path / "custom.log").read_text(encoding="utf-8")

    nlog.configure_logger(
        None,
        config(NACOS_LOG_CONSOLE_ENABLED=False, NACOS_LOG_FILE_ENABLED=False),
    )
    assert owned(logger, "file") == []
    assert len(owned(logger, "null")) == 1


@pytest.mark.parametrize(
    "key, value",
    [
        ("NACOS_LOG_LEVEL", "TRACE"),
        ("NACOS_LOG_FORMAT", "%(missing)s"),
        ("NACOS_LOG_PATH", ""),
        ("NACOS_LOG_PATH", 123),
        ("NACOS_LOG_FILENAME", ""),
        ("NACOS_LOG_FILENAME", "nested/log.txt"),
        ("NACOS_LOG_FILENAME", ".."),
        ("NACOS_LOG_MAX_BYTES", True),
        ("NACOS_LOG_MAX_BYTES", -1),
        ("NACOS_LOG_MAX_BYTES", 1.5),
        ("NACOS_LOG_BACKUP_COUNT", float("inf")),
    ],
)
def test_enabled_logging_validation(key, value):
    with pytest.raises(NacosLoggingError):
        nlog.validate_logging_config(config(**{key: value}))


def test_disabled_capabilities_ignore_their_settings(tmp_path):
    disabled = load_config(
        {
            "NACOS_LOG_ENABLED": False,
            "NACOS_LOG_LEVEL": object(),
            "NACOS_LOG_FILENAME": "../bad.log",
            "NACOS_LOG_MAX_BYTES": True,
        }
    )
    nlog.configure_logger(None, disabled)
    package_logger = logging.getLogger(nlog.FASTAPI_NACOS_LOGGER_NAME)
    assert package_logger.disabled is True
    assert len(owned(package_logger, "null")) == 1

    no_file = config(
        NACOS_LOG_FILE_ENABLED=False,
        NACOS_LOG_PATH=str(tmp_path / "absent"),
        NACOS_LOG_FILENAME="../bad.log",
        NACOS_LOG_MAX_BYTES=True,
    )
    nlog.configure_logger(None, no_file)
    assert not (tmp_path / "absent").exists()


def test_existing_file_is_not_accepted_as_directory(tmp_path):
    path = tmp_path / "legacy"
    path.write_text("keep", encoding="utf-8")
    with pytest.raises(NacosLoggingError, match="directory"):
        nlog.validate_logging_config(config(NACOS_LOG_PATH=str(path)))
    assert path.read_text(encoding="utf-8") == "keep"


def test_sdk_loggers_drop_untrusted_handlers():
    for name in nlog.SDK_LOGGER_NAMES:
        logger = logging.getLogger(name)
        untrusted = logging.StreamHandler()
        logger.addHandler(untrusted)
    nlog.configure_sdk_loggers()
    for name in nlog.SDK_LOGGER_NAMES:
        logger = logging.getLogger(name)
        assert logger.disabled is True
        assert logger.propagate is False
        assert all(isinstance(handler, logging.NullHandler) for handler in logger.handlers)


def test_public_handler_helpers_add_update_and_remove(tmp_path):
    logger = logging.Logger("isolated")
    formatter = logging.Formatter("%(levelname)s:%(message)s")
    nlog.ensure_null_handler(logger)
    nlog.ensure_null_handler(logger)
    assert len(owned(logger, "null")) == 1

    nlog.add_console_handler_once(logger, formatter, logging.INFO)
    nlog.add_console_handler_once(logger, formatter, logging.DEBUG)
    assert len(owned(logger, "console")) == 1
    assert owned(logger, "console")[0].level == logging.DEBUG

    log_file = tmp_path / "direct.log"
    assert nlog.add_file_handler_once(
        logger, str(log_file), formatter, logging.INFO, None, 0
    )
    assert nlog.add_file_handler_once(
        logger, str(log_file), formatter, logging.ERROR, None, 0
    )
    assert len(owned(logger, "file")) == 1
    assert owned(logger, "file")[0].level == logging.ERROR

    for handler in list(logger.handlers):
        handler.close()


def test_default_sdk_file_handler_is_removed(monkeypatch, tmp_path):
    default_path = tmp_path / "nacos-client-python.log"
    monkeypatch.setattr(nlog, "DEFAULT_SDK_LOG_PATH", str(default_path))
    logger = logging.Logger("sdk-test")
    default_handler = logging.FileHandler(str(default_path), encoding="utf-8")
    other_handler = logging.StreamHandler()
    logger.addHandler(default_handler)
    logger.addHandler(other_handler)
    nlog.remove_nacos_default_file_handlers(logger)
    assert default_handler not in logger.handlers
    assert other_handler in logger.handlers
    other_handler.close()


def test_file_handler_creation_failures_are_wrapped(monkeypatch, tmp_path):
    logger = logging.Logger("broken-file")
    formatter = logging.Formatter("%(message)s")
    monkeypatch.setattr(
        nlog,
        "_create_file_handler",
        MagicMock(side_effect=OSError("private")),
    )
    with pytest.raises(NacosLoggingError, match="log file handler"):
        nlog.add_file_handler_once(
            logger,
            str(tmp_path / "broken.log"),
            formatter,
            logging.INFO,
            100,
            1,
        )
    with pytest.raises(NacosLoggingError, match="log file handler"):
        nlog.configure_named_logger(
            logger,
            {
                "enabled": True,
                "level": logging.INFO,
                "formatter": formatter,
                "console_enabled": True,
                "file_enabled": True,
                "file": str(tmp_path / "broken.log"),
                "propagate": False,
                "max_bytes": 100,
                "backup_count": 1,
            },
        )


@pytest.mark.parametrize("value", [None, "", 12])
def test_invalid_log_formats(value):
    with pytest.raises(NacosLoggingError):
        nlog.validate_logging_config(config(NACOS_LOG_FORMAT=value))
