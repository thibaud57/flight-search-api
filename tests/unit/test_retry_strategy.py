"""Tests unitaires RetryStrategy."""

from unittest.mock import patch

import pytest
from tenacity import retry

from app.exceptions import CaptchaDetectedError, NetworkError
from app.services.retry_strategy import RetryStrategy


def test_retry_on_network_error():
    """Retry declenche sur NetworkError."""
    # Arrange
    call_count = 0

    @retry(**RetryStrategy.get_crawler_retry())
    def mock_function():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise NetworkError(url="https://example.com", status_code=503)
        return "success"

    # Act
    with patch("asyncio.sleep"):
        result = mock_function()

    # Assert
    assert call_count == 3
    assert result == "success"


def test_retry_on_captcha_detected():
    """Retry declenche sur CaptchaDetectedError."""
    # Arrange
    call_count = 0

    @retry(**RetryStrategy.get_crawler_retry())
    def mock_function():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise CaptchaDetectedError(
                url="https://example.com", captcha_type="recaptcha_v2"
            )
        return "success"

    # Act
    with patch("asyncio.sleep"):
        result = mock_function()

    # Assert
    assert call_count == 2
    assert result == "success"


def test_no_retry_on_validation_error():
    """Pas de retry sur ValidationError."""
    # Arrange
    call_count = 0

    @retry(**RetryStrategy.get_crawler_retry())
    def mock_function():
        nonlocal call_count
        call_count += 1
        raise ValueError("Validation failed")

    # Act & Assert
    with pytest.raises(ValueError):
        mock_function()

    assert call_count == 1


def test_exponential_backoff_timing():
    """Wait time augmente exponentiellement."""
    # Arrange
    call_count = 0
    wait_times = []

    original_sleep = None

    def capture_sleep(seconds):
        wait_times.append(seconds)

    @retry(**RetryStrategy.get_crawler_retry())
    def mock_function():
        nonlocal call_count
        call_count += 1
        raise NetworkError(url="https://example.com", status_code=503)

    # Act
    import time

    original_sleep = time.sleep
    time.sleep = capture_sleep
    try:
        mock_function()
    except NetworkError:
        pass
    finally:
        time.sleep = original_sleep

    # Assert
    assert call_count == 3
    assert len(wait_times) == 2
    assert 2 <= wait_times[0] <= 8
    assert 4 <= wait_times[1] <= 12


def test_max_retries_exceeded():
    """Max retries atteint leve NetworkError finale."""
    # Arrange
    call_count = 0

    @retry(**RetryStrategy.get_crawler_retry())
    def mock_function():
        nonlocal call_count
        call_count += 1
        raise NetworkError(url="https://example.com", status_code=503)

    # Act & Assert
    with patch("tenacity.nap.sleep"), pytest.raises(NetworkError):
        mock_function()

    assert call_count == 3


def test_jitter_randomness():
    """Jitter ajoute randomness aux wait times."""
    # Arrange
    wait_times_all = []

    def capture_sleep(seconds):
        wait_times_all.append(seconds)

    @retry(**RetryStrategy.get_crawler_retry())
    def mock_function():
        raise NetworkError(url="https://example.com", status_code=503)

    # Act
    import contextlib
    import time

    original_sleep = time.sleep
    time.sleep = capture_sleep
    try:
        for _ in range(2):
            with contextlib.suppress(NetworkError):
                mock_function()
    finally:
        time.sleep = original_sleep

    # Assert
    assert len(wait_times_all) >= 4
    for wait_time in wait_times_all:
        assert 0 <= wait_time <= 60


def test_before_sleep_callback_logging(caplog):
    """Before_sleep callback appele a chaque retry."""
    # Arrange
    import logging

    caplog.set_level(logging.WARNING)
    call_count = 0

    @retry(**RetryStrategy.get_crawler_retry())
    def mock_function(url: str):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise CaptchaDetectedError(url=url, captcha_type="recaptcha_v2")
        return "success"

    # Act
    with patch("tenacity.nap.sleep"):
        mock_function("https://example.com")

    # Assert
    assert call_count == 3
    warning_logs = [
        record for record in caplog.records if record.levelname == "WARNING"
    ]
    assert len(warning_logs) == 2
    assert "attempt_number" in str(warning_logs[0].__dict__)
    assert "attempt_number" in str(warning_logs[1].__dict__)


def test_retry_success_after_failures():
    """Succes apres N echecs sans lever exception finale."""
    # Arrange
    call_count = 0

    @retry(**RetryStrategy.get_crawler_retry())
    def mock_function():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise NetworkError(url="https://example.com", status_code=503)
        return "success"

    # Act
    with patch("tenacity.nap.sleep"):
        result = mock_function()

    # Assert
    assert call_count == 3
    assert result == "success"
