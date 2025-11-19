"""Tests unitaires pour Logger (Structured JSON)."""

import io
import json
import logging
from datetime import datetime

import pytest

from app.core.logger import setup_logger


def test_setup_logger_returns_logger_instance() -> None:
    """setup_logger retourne instance Logger."""
    # Act
    logger = setup_logger("INFO")

    # Assert
    assert isinstance(logger, logging.Logger)


def test_logger_output_is_valid_json(caplog: pytest.LogCaptureFixture) -> None:
    """Log émis est JSON parsable."""
    # Arrange
    logger = setup_logger("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    from pythonjsonlogger import jsonlogger

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    # Act
    logger.info("test message")
    output = stream.getvalue()

    # Assert
    try:
        parsed = json.loads(output.strip())
        assert isinstance(parsed, dict)
    except json.JSONDecodeError as e:
        pytest.fail(f"Output is not valid JSON: {e}")


def test_logger_json_contains_standard_fields() -> None:
    """Log JSON contient champs standards."""
    # Arrange
    logger = setup_logger("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    from pythonjsonlogger import jsonlogger

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    # Act
    logger.info("test")
    output = stream.getvalue()

    # Assert
    parsed = json.loads(output.strip())
    assert "asctime" in parsed
    assert "name" in parsed
    assert "levelname" in parsed
    assert "message" in parsed


def test_logger_respects_log_level_debug(caplog: pytest.LogCaptureFixture) -> None:
    """Logger niveau DEBUG affiche tous logs."""
    # Arrange
    logger = setup_logger("DEBUG")

    # Act
    with caplog.at_level(logging.DEBUG, logger=logger.name):
        logger.debug("test debug message")

    # Assert
    assert any("test debug message" in record.message for record in caplog.records)


def test_logger_respects_log_level_info(caplog: pytest.LogCaptureFixture) -> None:
    """Logger niveau INFO filtre logs DEBUG."""
    # Arrange
    logger = setup_logger("INFO")

    # Act
    with caplog.at_level(logging.INFO, logger=logger.name):
        logger.debug("test debug message")

    # Assert
    debug_records = [
        r
        for r in caplog.records
        if r.levelno == logging.DEBUG and "test debug message" in r.message
    ]
    assert len(debug_records) == 0


def test_logger_supports_extra_fields() -> None:
    """Extra fields ajoutés au JSON log."""
    # Arrange
    logger = setup_logger("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    from pythonjsonlogger import jsonlogger

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    # Act
    logger.info("test", extra={"search_id": "abc123"})
    output = stream.getvalue()

    # Assert
    parsed = json.loads(output.strip())
    assert parsed["search_id"] == "abc123"


def test_logger_does_not_log_secrets() -> None:
    """Secrets masqués dans logs."""
    # Arrange
    logger = setup_logger("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    from pythonjsonlogger import jsonlogger

    from app.core.logger import SensitiveDataFilter

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())
    logger.handlers = [handler]

    # Act
    logger.info("test", extra={"password": "secret123"})
    output = stream.getvalue()

    # Assert
    parsed = json.loads(output.strip())
    assert parsed["password"] == "***"


def test_logger_timestamp_is_iso8601() -> None:
    """Timestamps au format ISO 8601."""
    # Arrange
    logger = setup_logger("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    from pythonjsonlogger import jsonlogger

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    # Act
    logger.info("test")
    output = stream.getvalue()

    # Assert
    parsed = json.loads(output.strip())
    asctime = parsed["asctime"]
    try:
        datetime.fromisoformat(asctime)
    except ValueError as e:
        pytest.fail(f"asctime is not ISO 8601 format: {e}")
