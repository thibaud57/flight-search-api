import math
from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.google_flight_dto import GoogleFlightDTO


def validate_iso_date(value: str) -> str:
    """Valide format ISO 8601 (YYYY-MM-DD)."""
    try:
        datetime.fromisoformat(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid ISO 8601 date format: {value}") from e
    return value


class DateRange(BaseModel):
    """Plage de dates pour recherche vols."""

    model_config = ConfigDict(extra="forbid")

    start: str
    end: str

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_iso_format(cls, v: str) -> str:
        """Valide format ISO 8601 (YYYY-MM-DD)."""
        return validate_iso_date(v)

    @model_validator(mode="after")
    def validate_dates_coherent(self) -> Self:
        """Valide que end >= start et start >= aujourd'hui."""
        start_date = date.fromisoformat(self.start)
        end_date = date.fromisoformat(self.end)

        if end_date < start_date:
            raise ValueError("End date must be greater than or equal to start date")

        if start_date < date.today():
            raise ValueError("Start date must be today or in the future")

        return self


class SearchRequest(BaseModel):
    """Requête recherche vols multi-city avec URL template Google Flights."""

    model_config = ConfigDict(extra="forbid")

    template_url: Annotated[
        str, "URL Google Flights template (itinéraire et filtres fixés)"
    ]
    segments_date_ranges: Annotated[
        list[DateRange], "Plages dates par segment (2-5 segments)"
    ]

    @field_validator("template_url", mode="after")
    @classmethod
    def validate_template_url(cls, v: str) -> str:
        """Valide URL Google Flights avec paramètre tfs."""
        if not v.startswith("https://www.google.com/travel/flights"):
            raise ValueError("URL must be a valid Google Flights URL")
        if "tfs=" not in v:
            raise ValueError("URL template must contain 'tfs=' parameter")
        return v

    @field_validator("segments_date_ranges", mode="after")
    @classmethod
    def validate_segments_count(cls, v: list[DateRange]) -> list[DateRange]:
        """Valide 2 à 5 segments."""
        if len(v) < 2:
            raise ValueError("At least 2 segments required for multi-city search")
        if len(v) > 5:
            raise ValueError("Maximum 5 segments allowed")
        return v

    @model_validator(mode="after")
    def validate_date_ranges_max_days(self) -> Self:
        """Valide max 15 jours par segment."""
        for idx, date_range in enumerate(self.segments_date_ranges):
            start_date = date.fromisoformat(date_range.start)
            end_date = date.fromisoformat(date_range.end)
            days_diff = (end_date - start_date).days

            if days_diff > 15:
                raise ValueError(
                    f"Segment {idx + 1} date range too large: {days_diff} days. "
                    f"Max 15 days per segment."
                )

        return self

    @model_validator(mode="after")
    def validate_segments_chronological_order(self) -> Self:
        """Valide que les segments sont chronologiques sans chevauchement."""
        if len(self.segments_date_ranges) < 2:
            return self

        for i in range(len(self.segments_date_ranges) - 1):
            current_end = date.fromisoformat(self.segments_date_ranges[i].end)
            next_start = date.fromisoformat(self.segments_date_ranges[i + 1].start)

            if next_start < current_end:
                raise ValueError(
                    f"Segment {i + 2} overlaps with segment {i + 1}: "
                    f"segment {i + 2} starts on {self.segments_date_ranges[i + 1].start} "
                    f"but segment {i + 1} ends on {self.segments_date_ranges[i].end}. "
                    f"Each segment must start on or after the previous segment's end date."
                )

        return self

    @model_validator(mode="after")
    def validate_explosion_combinatoire(self) -> Self:
        """Valide max 1000 combinaisons totales avec message UX-friendly."""
        days_per_segment = []

        for date_range in self.segments_date_ranges:
            start_date = date.fromisoformat(date_range.start)
            end_date = date.fromisoformat(date_range.end)
            days_diff = (end_date - start_date).days + 1
            days_per_segment.append(days_diff)

        total_combinations = math.prod(days_per_segment)

        if total_combinations > 1000:
            max_days_index = days_per_segment.index(max(days_per_segment))
            max_days = days_per_segment[max_days_index]

            raise ValueError(
                f"Too many combinations: {total_combinations}. Max 1000 allowed.\n"
                f"Current ranges: {days_per_segment} days per segment.\n"
                f"Suggestion: Reduce segment {max_days_index + 1} (currently {max_days} days)."
            )

        return self


class DateCombination(BaseModel):
    """Combinaison dates pour itineraire multi-city fixe."""

    model_config = ConfigDict(extra="forbid")

    segment_dates: list[str]

    @field_validator("segment_dates", mode="after")
    @classmethod
    def validate_segment_dates(cls, v: list[str]) -> list[str]:
        """Valide format ISO 8601 et min 2 dates."""
        if len(v) < 2:
            raise ValueError("At least 2 segment dates required")
        return [validate_iso_date(d) for d in v]


class CombinationResult(BaseModel):
    """Resultat intermediaire pour une combinaison dates."""

    model_config = ConfigDict(extra="forbid")

    date_combination: DateCombination
    best_flight: GoogleFlightDTO
