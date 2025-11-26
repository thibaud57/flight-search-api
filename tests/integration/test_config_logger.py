"""Tests intégration pour Settings et Logger."""

import io
import logging

import pytest
from pydantic import ValidationError
from pythonjsonlogger import jsonlogger

from app.core import setup_logger
from tests.fixtures.helpers import (
    assert_log_captured,
    assert_log_contains_fields,
    parse_log_output,
)


def test_settings_loaded_at_app_startup(settings_env_factory) -> None:
    """Settings instance accessible sans erreur."""
    settings = settings_env_factory(
        LOG_LEVEL="INFO",
        PROXY_ROTATION_ENABLED="true",
        CAPTCHA_DETECTION_ENABLED="true",
    )

    assert settings.LOG_LEVEL == "INFO"
    assert settings.DECODO_USERNAME == "testuser"
    assert settings.DECODO_PASSWORD.get_secret_value() == "password123"
    assert settings.PROXY_ROTATION_ENABLED is True


def test_app_refuses_startup_with_invalid_config(settings_env_factory) -> None:
    """ValidationError levee avec config invalide."""
    with pytest.raises(ValidationError):
        settings_env_factory(LOG_LEVEL="INVALID")


def test_logger_functional_with_settings_log_level(
    settings_env_factory, caplog: pytest.LogCaptureFixture
) -> None:
    """Logger affiche logs DEBUG avec Settings.LOG_LEVEL=DEBUG."""
    settings = settings_env_factory(LOG_LEVEL="DEBUG")

    logger = setup_logger(settings.LOG_LEVEL)
    with caplog.at_level(logging.DEBUG, logger=logger.name):
        logger.debug("test debug log")

    assert_log_captured(caplog, "test debug log", logging.DEBUG)


def test_logs_parsable_by_json_parser() -> None:
    """Tous logs parsables par json.loads() sans erreur."""
    logger = setup_logger("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    logger.info("test message 1")
    logger.warning("test message 2", extra={"key": "value"})

    lines = stream.getvalue().strip().split("\n")
    for line in lines:
        parsed = parse_log_output(io.StringIO(line))
        assert_log_contains_fields(parsed, "message")
