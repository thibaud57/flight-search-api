from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.google_flight_dto import GoogleFlightDTO


class DateRange(BaseModel):
    """Plage de dates pour recherche vols."""

    start: str
    end: str

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_iso_format(cls, v: str) -> str:
        """Valide format ISO 8601 (YYYY-MM-DD)."""
        try:
            datetime.fromisoformat(v)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Date must be in ISO 8601 format (YYYY-MM-DD): {v}"
            ) from e
        return v

    @model_validator(mode="after")
    def validate_dates_coherent(self) -> "DateRange":
        """Valide que end >= start et start >= aujourd'hui."""
        start_date = date.fromisoformat(self.start)
        end_date = date.fromisoformat(self.end)

        if end_date < start_date:
            raise ValueError("End date must be greater than or equal to start date")

        if start_date < date.today():
            raise ValueError("Start date must be today or in the future")

        return self


class FlightSegment(BaseModel):
    """Segment de vol dans itinéraire multi-city."""

    from_city: Annotated[str, "Ville(s) départ (ex: 'Paris' ou 'Paris,Francfort')"]
    to_city: Annotated[str, "Ville(s) arrivée (ex: 'Tokyo' ou 'Tokyo,Osaka')"]
    date_range: DateRange

    @field_validator("from_city", "to_city", mode="after")
    @classmethod
    def validate_city_length(cls, v: str) -> str:
        """Valide min 2 caractères après trim."""
        trimmed = v.strip()
        if len(trimmed) < 2:
            raise ValueError("City name must be at least 2 characters")
        return trimmed

    @model_validator(mode="after")
    def validate_date_range_max_days(self) -> "FlightSegment":
        """Valide max 15 jours par segment."""
        start_date = date.fromisoformat(self.date_range.start)
        end_date = date.fromisoformat(self.date_range.end)
        days_diff = (end_date - start_date).days

        if days_diff > 15:
            raise ValueError(
                f"Date range too large: {days_diff} days. Max 15 days per segment."
            )

        return self


class SearchRequest(BaseModel):
    """Requête de recherche vols multi-city (itinéraire segments fixe, dates flexibles)."""

    segments: Annotated[list[FlightSegment], "Liste segments itinéraire (2-5 segments)"]

    @field_validator("segments", mode="after")
    @classmethod
    def validate_segments_count(cls, v: list[FlightSegment]) -> list[FlightSegment]:
        """Valide 2 à 5 segments."""
        if len(v) < 2:
            raise ValueError("At least 2 segments required for multi-city search")
        if len(v) > 5:
            raise ValueError("Maximum 5 segments allowed")
        return v

    @model_validator(mode="after")
    def validate_explosion_combinatoire(self) -> "SearchRequest":
        """Valide max 1000 combinaisons totales avec message UX-friendly."""
        days_per_segment = []

        for segment in self.segments:
            start_date = date.fromisoformat(segment.date_range.start)
            end_date = date.fromisoformat(segment.date_range.end)
            days_diff = (end_date - start_date).days + 1
            days_per_segment.append(days_diff)

        total_combinations = 1
        for days in days_per_segment:
            total_combinations *= days

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
        for d in v:
            try:
                datetime.fromisoformat(d)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid ISO 8601 date format: {d}") from e
        return v


class CombinationResult(BaseModel):
    """Resultat intermediaire pour une combinaison dates."""

    model_config = ConfigDict(extra="forbid")

    date_combination: DateCombination
    flights: list[GoogleFlightDTO]
    total_price: float = 0.0
    total_duration_minutes: int = 0
    total_stops: int = 0

    @field_validator("flights", mode="after")
    @classmethod
    def validate_flights_not_empty(
        cls, v: list[GoogleFlightDTO]
    ) -> list[GoogleFlightDTO]:
        """Valide au moins 1 vol."""
        if len(v) < 1:
            raise ValueError("At least 1 flight required")
        return v

    @model_validator(mode="after")
    def compute_totals(self) -> "CombinationResult":
        """Calcule automatiquement totaux depuis flights."""
        self.total_price = sum(f.price for f in self.flights)
        self.total_duration_minutes = sum(
            self._parse_duration(f.duration) for f in self.flights
        )
        self.total_stops = sum(f.stops or 0 for f in self.flights)
        return self

    def _parse_duration(self, duration: str) -> int:
        """Parse duree en minutes depuis string (ex: '10h 15min')."""
        if not duration:
            return 0
        total = 0
        import re

        hours_match = re.search(r"(\d+)\s*h", duration.lower())
        mins_match = re.search(r"(\d+)\s*m", duration.lower())
        if hours_match:
            total += int(hours_match.group(1)) * 60
        if mins_match:
            total += int(mins_match.group(1))
        return total
