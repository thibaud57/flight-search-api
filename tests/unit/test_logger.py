"""Tests unitaires pour Logger (Structured JSON)."""

import io
import logging
from datetime import datetime
from typing import Protocol

import pytest
from pythonjsonlogger import jsonlogger

from app.core.logger import SensitiveDataFilter, setup_logger
from tests.fixtures.helpers import (
    assert_log_captured,
    assert_log_contains_fields,
    assert_log_field_value,
    assert_log_not_captured,
    parse_log_output,
)


class LoggerStreamFactory(Protocol):
    """Protocol pour fixture logger_with_json_stream."""

    def __call__(
        self, datefmt: str | None = None
    ) -> tuple[logging.Logger, io.StringIO]: ...


@pytest.fixture
def logger_with_json_stream():
    """Logger avec handler JSON + StringIO pour capture output."""

    def _create(datefmt: str | None = None) -> tuple[logging.Logger, io.StringIO]:
        logger = setup_logger("INFO")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        formatter = jsonlogger.JsonFormatter(  # type: ignore[attr-defined]
            "%(asctime)s %(name)s %(levelname)s %(message)s", datefmt=datefmt
        )
        handler.setFormatter(formatter)
        logger.handlers = [handler]
        return logger, stream

    yield _create


def test_setup_logger_returns_logger_instance() -> None:
    """setup_logger retourne instance Logger."""
    logger = setup_logger("INFO")

    assert isinstance(logger, logging.Logger)


def test_logger_output_is_valid_json(
    logger_with_json_stream: LoggerStreamFactory,
) -> None:
    """Log émis est JSON parsable."""
    logger, stream = logger_with_json_stream()

    logger.info("test message")
    parsed = parse_log_output(stream)

    assert isinstance(parsed, dict)


def test_logger_json_contains_standard_fields(
    logger_with_json_stream: LoggerStreamFactory,
) -> None:
    """Log JSON contient champs standards."""
    logger, stream = logger_with_json_stream()

    logger.info("test")
    parsed = parse_log_output(stream)

    assert_log_contains_fields(parsed, "asctime", "name", "levelname", "message")


def test_logger_respects_log_level_debug(caplog: pytest.LogCaptureFixture) -> None:
    """Logger niveau DEBUG affiche tous logs."""
    logger = setup_logger("DEBUG")

    with caplog.at_level(logging.DEBUG, logger=logger.name):
        logger.debug("test debug message")

    assert_log_captured(caplog, "test debug message")


def test_logger_respects_log_level_info(caplog: pytest.LogCaptureFixture) -> None:
    """Logger niveau INFO filtre logs DEBUG."""
    logger = setup_logger("INFO")

    with caplog.at_level(logging.INFO, logger=logger.name):
        logger.debug("test debug message")

    assert_log_not_captured(caplog, "test debug message", level=logging.DEBUG)


def test_logger_supports_extra_fields(
    logger_with_json_stream: LoggerStreamFactory,
) -> None:
    """Extra fields ajoutés au JSON log."""
    logger, stream = logger_with_json_stream()

    logger.info("test", extra={"search_id": "abc123"})
    parsed = parse_log_output(stream)

    assert_log_field_value(parsed, "search_id", "abc123")


def test_logger_does_not_log_secrets(
    logger_with_json_stream: LoggerStreamFactory,
) -> None:
    """Secrets masqués dans logs."""
    logger, stream = logger_with_json_stream()
    logger.handlers[0].addFilter(SensitiveDataFilter())

    logger.info("test", extra={"password": "secret123"})
    parsed = parse_log_output(stream)

    assert_log_field_value(parsed, "password", "***")


def test_logger_timestamp_is_iso8601(
    logger_with_json_stream: LoggerStreamFactory,
) -> None:
    """Timestamps au format ISO 8601."""
    logger, stream = logger_with_json_stream(datefmt="%Y-%m-%dT%H:%M:%S")

    logger.info("test")
    parsed = parse_log_output(stream)

    asctime = parsed["asctime"]
    try:
        datetime.fromisoformat(asctime)
    except ValueError as e:
        pytest.fail(f"asctime is not ISO 8601 format: {e}")
