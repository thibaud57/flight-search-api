"""Tests intégration pour Settings et Logger."""

import io
import json
import logging

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.logger import setup_logger


def test_settings_loaded_at_app_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings instance accessible sans erreur."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "testuser")
    monkeypatch.setenv("DECODO_PASSWORD", "testpass123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "fr.decodo.com:40000")
    monkeypatch.setenv("PROXY_ROTATION_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_DETECTION_ENABLED", "true")

    settings = Settings()

    assert settings.LOG_LEVEL == "INFO"
    assert settings.DECODO_USERNAME == "testuser"
    assert settings.DECODO_PASSWORD.get_secret_value() == "testpass123"
    assert settings.PROXY_ROTATION_ENABLED is True


def test_app_refuses_startup_with_invalid_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ValidationError levee avec config invalide."""
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    monkeypatch.setenv("DECODO_USERNAME", "testuser")
    monkeypatch.setenv("DECODO_PASSWORD", "testpass123")

    with pytest.raises(ValidationError):
        Settings()


def test_logger_functional_with_settings_log_level(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Logger affiche logs DEBUG avec Settings.LOG_LEVEL=DEBUG."""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DECODO_USERNAME", "testuser")
    monkeypatch.setenv("DECODO_PASSWORD", "testpass123")
    settings = Settings()

    logger = setup_logger(settings.LOG_LEVEL)
    with caplog.at_level(logging.DEBUG, logger=logger.name):
        logger.debug("test debug log")

    assert any("test debug log" in record.message for record in caplog.records)


def test_logs_parsable_by_json_parser() -> None:
    """Tous logs parsables par json.loads() sans erreur."""
    logger = setup_logger("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    from pythonjsonlogger import jsonlogger

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    logger.info("test message 1")
    logger.warning("test message 2", extra={"key": "value"})
    output = stream.getvalue()

    lines = output.strip().split("\n")
    for line in lines:
        try:
            parsed = json.loads(line)
            assert isinstance(parsed, dict)
            assert "message" in parsed
        except json.JSONDecodeError as e:
            pytest.fail(f"Line is not valid JSON: {line}, error: {e}")
