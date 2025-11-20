from typing import Annotated, Literal

from pydantic import BaseModel, field_validator, model_validator


class HealthResponse(BaseModel):
    """Schéma response endpoint health check."""

    status: Literal["ok", "error"]


class FlightResult(BaseModel):
    """Résultat individuel vol (1 sur 10 retournés)."""

    price: Annotated[float, "Prix total itinéraire en EUR"]
    airline: str
    departure_date: str
    segments: list[dict[str, str]]

    @field_validator("price", mode="after")
    @classmethod
    def validate_price_positive(cls, v: float) -> float:
        """Valide prix >= 0."""
        if v < 0:
            raise ValueError("Price must be >= 0")
        return v


class SearchStats(BaseModel):
    """Statistiques métadonnées recherche."""

    total_results: int
    search_time_ms: int
    segments_count: int


class SearchResponse(BaseModel):
    """Réponse API contenant top 10 résultats + stats."""

    results: Annotated[list[FlightResult], "Top 10 résultats triés par prix croissant"]
    search_stats: SearchStats

    @field_validator("results", mode="after")
    @classmethod
    def validate_max_10_results(cls, v: list[FlightResult]) -> list[FlightResult]:
        """Valide max 10 results."""
        if len(v) > 10:
            raise ValueError("Maximum 10 results allowed")
        return v

    @model_validator(mode="after")
    def validate_results_sorted(self) -> "SearchResponse":
        """Valide results triés par prix croissant."""
        if len(self.results) > 1:
            for i in range(len(self.results) - 1):
                if self.results[i].price > self.results[i + 1].price:
                    raise ValueError(
                        "Results must be sorted by price (ascending order)"
                    )
        return self
