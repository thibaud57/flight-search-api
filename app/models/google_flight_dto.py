"""DTO pour données extraites depuis Google Flights."""

from typing import Any

from pydantic import BaseModel, ConfigDict, model_serializer


class GoogleFlightDTO(BaseModel):
    """Modèle Pydantic d'un vol extrait depuis Google Flights."""

    model_config = ConfigDict(extra="forbid")

    @model_serializer(mode="wrap")
    def _serialize(self, serializer: Any, info: Any) -> dict[str, Any]:
        data = serializer(self)
        return {k: v for k, v in data.items() if v is not None}

    price: float | None = None
    airline: str
    departure_time: str
    arrival_time: str
    duration: str
    stops: int | None = None
    departure_airport: str | None = None
    arrival_airport: str | None = None
