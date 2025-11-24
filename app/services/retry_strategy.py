"""Configuration Tenacity centralisee pour retry logic production."""

from __future__ import annotations

import logging
from typing import Any

from tenacity import (
    RetryCallState,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from app.exceptions import CaptchaDetectedError, NetworkError

logger = logging.getLogger(__name__)


def log_retry_attempt(retry_state: RetryCallState) -> None:
    """Callback Tenacity before_sleep pour logging structure retry attempts."""
    try:
        attempt_number = retry_state.attempt_number
        exception = retry_state.outcome.exception() if retry_state.outcome else None
        wait_time = retry_state.next_action.sleep if retry_state.next_action else 0.0

        url = "unknown"
        if retry_state.args and len(retry_state.args) >= 2:
            url = retry_state.args[1]

        exception_type = type(exception).__name__ if exception else "UnknownError"
        exception_message = str(exception) if exception else "No exception details"

        max_attempts = 3
        attempts_remaining = max_attempts - attempt_number

        logger.warning(
            "Retry attempt triggered",
            extra={
                "url": url,
                "exception_type": exception_type,
                "exception_message": exception_message,
                "attempt_number": attempt_number,
                "attempts_remaining": attempts_remaining,
                "wait_time_seconds": round(wait_time, 2),
            },
        )
    except Exception as e:
        logger.debug(f"Before_sleep callback failed: {e}")


class RetryStrategy:
    """Configuration Tenacity centralisee pour retry logic production."""

    @staticmethod
    def get_crawler_retry() -> dict[str, Any]:
        """Retourne configuration retry optimisee CrawlerService."""
        logger.debug(
            "Creating retry configuration",
            extra={
                "max_attempts": 3,
                "wait_strategy": "random_exponential",
                "min_wait": 4,
                "max_wait": 60,
            },
        )

        return {
            "stop": stop_after_attempt(3),
            "wait": wait_random_exponential(multiplier=2, min=4, max=60),
            "retry": retry_if_exception_type((CaptchaDetectedError, NetworkError)),
            "before_sleep": log_retry_attempt,
            "reraise": True,
        }
