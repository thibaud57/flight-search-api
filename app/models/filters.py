"""Modèles de filtrage per-segment pour vols."""

from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core.constants import DURATION_PATTERN_HHMM
from app.utils.duration import parse_duration


class SegmentFilters(BaseModel):
    """Filtres applicables à un segment de voyage."""

    model_config = ConfigDict(extra="forbid")

    max_duration: str | None = None
    max_stops: int | None = None
    min_layover_duration: str | None = None
    max_layover_duration: str | None = None

    @field_validator("max_duration", mode="after")
    @classmethod
    def validate_max_duration(cls, v: str | None) -> str | None:
        """Valide format HH:MM et limite max 24h."""
        if v is None:
            return v

        if not DURATION_PATTERN_HHMM.match(v):
            raise ValueError(
                f"Invalid duration format. Expected HH:MM (zero-padded), got '{v}'"
            )

        minutes = parse_duration(v)
        if minutes > 1440:
            raise ValueError(
                f"Max duration must be <= 1440 minutes (24h), got {minutes}"
            )

        return v

    @field_validator("min_layover_duration", mode="after")
    @classmethod
    def validate_min_layover_duration(cls, v: str | None) -> str | None:
        """Valide format HH:MM et limite max 12h."""
        if v is None:
            return v

        if not DURATION_PATTERN_HHMM.match(v):
            raise ValueError(
                f"Invalid duration format. Expected HH:MM (zero-padded), got '{v}'"
            )

        minutes = parse_duration(v)
        if minutes > 720:
            raise ValueError(
                f"Min layover duration must be <= 720 minutes (12h), got {minutes}"
            )

        return v

    @field_validator("max_layover_duration", mode="after")
    @classmethod
    def validate_max_layover_duration(cls, v: str | None) -> str | None:
        """Valide format HH:MM et limite max 24h."""
        if v is None:
            return v

        if not DURATION_PATTERN_HHMM.match(v):
            raise ValueError(
                f"Invalid duration format. Expected HH:MM (zero-padded), got '{v}'"
            )

        minutes = parse_duration(v)
        if minutes > 1440:
            raise ValueError(
                f"Max layover duration must be <= 1440 minutes (24h), got {minutes}"
            )

        return v

    @field_validator("max_stops", mode="after")
    @classmethod
    def validate_max_stops(cls, v: int | None) -> int | None:
        """Valide range 0-3."""
        if v is None:
            return v

        if v < 0 or v > 3:
            raise ValueError(f"Max stops must be between 0 and 3, got {v}")

        return v

    @model_validator(mode="after")
    def validate_layover_range(self) -> Self:
        """Valide que max_layover > min_layover (strictement)."""
        if self.min_layover_duration is None or self.max_layover_duration is None:
            return self

        min_minutes = parse_duration(self.min_layover_duration)
        max_minutes = parse_duration(self.max_layover_duration)

        if max_minutes <= min_minutes:
            raise ValueError(
                f"max_layover_duration ({self.max_layover_duration}) must be strictly greater than "
                f"min_layover_duration ({self.min_layover_duration})"
            )

        return self
