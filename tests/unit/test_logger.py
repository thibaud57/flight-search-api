"""Tests unitaires pour Logger (Structured JSON)."""

import io
import json
import logging
from datetime import datetime

import pytest
from pythonjsonlogger import jsonlogger

from app.core.logger import SensitiveDataFilter, setup_logger


@pytest.fixture
def logger_with_json_stream():
    """Logger avec handler JSON + StringIO pour capture output."""
    logger = setup_logger("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    yield logger, stream

    logger.handlers.clear()


def test_setup_logger_returns_logger_instance() -> None:
    """setup_logger retourne instance Logger."""
    logger = setup_logger("INFO")

    assert isinstance(logger, logging.Logger)


def test_logger_output_is_valid_json(logger_with_json_stream) -> None:
    """Log émis est JSON parsable."""
    logger, stream = logger_with_json_stream

    logger.info("test message")
    output = stream.getvalue()

    try:
        parsed = json.loads(output.strip())
        assert isinstance(parsed, dict)
    except json.JSONDecodeError as e:
        pytest.fail(f"Output is not valid JSON: {e}")


def test_logger_json_contains_standard_fields(logger_with_json_stream) -> None:
    """Log JSON contient champs standards."""
    logger, stream = logger_with_json_stream

    logger.info("test")
    output = stream.getvalue()

    parsed = json.loads(output.strip())
    assert "asctime" in parsed
    assert "name" in parsed
    assert "levelname" in parsed
    assert "message" in parsed


def test_logger_respects_log_level_debug(caplog: pytest.LogCaptureFixture) -> None:
    """Logger niveau DEBUG affiche tous logs."""
    logger = setup_logger("DEBUG")

    with caplog.at_level(logging.DEBUG, logger=logger.name):
        logger.debug("test debug message")

    assert any("test debug message" in record.message for record in caplog.records)


def test_logger_respects_log_level_info(caplog: pytest.LogCaptureFixture) -> None:
    """Logger niveau INFO filtre logs DEBUG."""
    logger = setup_logger("INFO")

    with caplog.at_level(logging.INFO, logger=logger.name):
        logger.debug("test debug message")

    debug_records = [
        r
        for r in caplog.records
        if r.levelno == logging.DEBUG and "test debug message" in r.message
    ]
    assert len(debug_records) == 0


def test_logger_supports_extra_fields(logger_with_json_stream) -> None:
    """Extra fields ajoutés au JSON log."""
    logger, stream = logger_with_json_stream

    logger.info("test", extra={"search_id": "abc123"})
    output = stream.getvalue()

    parsed = json.loads(output.strip())
    assert parsed["search_id"] == "abc123"


def test_logger_does_not_log_secrets(logger_with_json_stream) -> None:
    """Secrets masqués dans logs."""
    logger, stream = logger_with_json_stream
    logger.handlers[0].addFilter(SensitiveDataFilter())

    logger.info("test", extra={"password": "secret123"})
    output = stream.getvalue()

    parsed = json.loads(output.strip())
    assert parsed["password"] == "***"


def test_logger_timestamp_is_iso8601() -> None:
    """Timestamps au format ISO 8601."""
    logger = setup_logger("INFO")
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.handlers = [handler]

    logger.info("test")
    output = stream.getvalue()

    parsed = json.loads(output.strip())
    asctime = parsed["asctime"]
    try:
        datetime.fromisoformat(asctime)
    except ValueError as e:
        pytest.fail(f"asctime is not ISO 8601 format: {e}")

    logger.handlers.clear()
