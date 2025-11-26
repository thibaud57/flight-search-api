"""Configuration polling Kayak."""

import logging

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class KayakPollingConfig(BaseSettings):
    """Configuration timing et comportement polling Kayak."""

    model_config = SettingsConfigDict(
        env_prefix="KAYAK_",
        extra="forbid",
    )

    page_load_timeout: int = 30
    first_results_wait: int = 20
    max_total_wait: int = 45
    poll_interval_min: int = 4
    poll_interval_max: int = 8

    @field_validator("poll_interval_max")
    @classmethod
    def validate_poll_interval_max(cls, v: int, info: ValidationInfo) -> int:
        """Vérifie poll_interval_max >= poll_interval_min."""
        data = info.data
        if "poll_interval_min" in data and v < data["poll_interval_min"]:
            raise ValueError(
                f"poll_interval_max ({v}) must be >= poll_interval_min ({data['poll_interval_min']})"
            )
        return v

    @field_validator("max_total_wait")
    @classmethod
    def validate_max_total_wait(cls, v: int) -> int:
        """Warning si max_total_wait < 30s."""
        if v < 30:
            logger.warning(
                "max_total_wait below recommended minimum",
                extra={"max_total_wait": v, "recommended_min": 30},
            )
        return v
