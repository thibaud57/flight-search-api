from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class HealthResponse(BaseModel):
    """Schéma response endpoint health check."""

    status: Literal["ok", "error"]


class FlightResult(BaseModel):
    """Resultat individuel vol (1 sur 10 retournes)."""

    price: Annotated[float, Field(ge=0.0), "Prix total en EUR"]
    airline: str
    departure_date: str
    route: list[str]


class SearchStats(BaseModel):
    """Statistiques metadonnees recherche."""

    total_results: int
    search_time_ms: int
    destinations_searched: list[str]


class SearchResponse(BaseModel):
    """Reponse API contenant top 10 resultats + stats."""

    results: Annotated[list[FlightResult], "Top 10 resultats tries par prix croissant"]
    search_stats: SearchStats

    @field_validator("results", mode="after")
    @classmethod
    def validate_max_results(cls, v: list[FlightResult]) -> list[FlightResult]:
        """Valide que results contient au plus 10 elements."""
        if len(v) > 10:
            raise ValueError(
                f"List should have at most 10 items after validation, not {len(v)}"
            )
        return v

    @model_validator(mode="after")
    def validate_results_sorted_by_price(self) -> "SearchResponse":
        """Valide que results est trie par prix croissant."""
        if len(self.results) > 1:
            for i in range(len(self.results) - 1):
                if self.results[i].price > self.results[i + 1].price:
                    raise ValueError(
                        "Results must be sorted by price in ascending order"
                    )
        return self
