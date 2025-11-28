"""DTO pour données extraites depuis Kayak."""

from typing import Any

from pydantic import BaseModel, ConfigDict, model_serializer


class LayoverInfo(BaseModel):
    """Information escale entre segments."""

    model_config = ConfigDict(extra="forbid")

    airport: str
    duration: str


class KayakFlightDTO(BaseModel):
    """Modèle Pydantic d'un vol extrait depuis Kayak."""

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
    departure_airport: str | None = None
    arrival_airport: str | None = None
    layovers: list[LayoverInfo] = []
