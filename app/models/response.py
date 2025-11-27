from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models import FlightDTO


class HealthResponse(BaseModel):
    """Schéma response endpoint health check."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"]


class FlightCombinationResult(BaseModel):
    """Résultat pour une combinaison de dates de segments (1 sur 10 retournés)."""

    model_config = ConfigDict(extra="forbid")

    segment_dates: Annotated[list[str], "Dates par segment (ISO 8601)"]
    flights: Annotated[
        list[FlightDTO],
        "Meilleurs vols pour cette combinaison (Google ou Kayak selon provider)",
    ]

    @field_validator("segment_dates", mode="after")
    @classmethod
    def validate_segment_dates_min(cls, v: list[str]) -> list[str]:
        """Valide min 2 dates."""
        if len(v) < 2:
            raise ValueError("At least 2 segment dates required")
        return v

    @field_validator("flights", mode="after")
    @classmethod
    def validate_flights_not_empty(cls, v: list[FlightDTO]) -> list[FlightDTO]:
        """Valide au moins 1 vol."""
        if len(v) == 0:
            raise ValueError("At least 1 flight required")
        return v


class SearchStats(BaseModel):
    """Statistiques métadonnées recherche."""

    model_config = ConfigDict(extra="forbid")

    total_results: int
    search_time_ms: int
    segments_count: int


class SearchResponse(BaseModel):
    """Réponse API contenant top 10 résultats + stats."""

    model_config = ConfigDict(extra="forbid")

    results: Annotated[
        list[FlightCombinationResult], "Top 10 résultats triés par prix croissant"
    ]
    search_stats: SearchStats

    @field_validator("results", mode="after")
    @classmethod
    def validate_max_10_results(
        cls, v: list[FlightCombinationResult]
    ) -> list[FlightCombinationResult]:
        """Valide max 10 results."""
        if len(v) > 10:
            raise ValueError("Maximum 10 results allowed")
        return v

    @model_validator(mode="after")
    def validate_results_sorted(self) -> Self:
        """Valide results triés par prix croissant (basé sur premier vol de chaque combinaison)."""
        if not all(
            a.flights[0].price <= b.flights[0].price
            for a, b in zip(self.results, self.results[1:], strict=False)
        ):
            raise ValueError("Results must be sorted by price (ascending order)")
        return self
