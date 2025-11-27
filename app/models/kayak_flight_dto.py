"""DTO pour données extraites depuis Kayak."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class LayoverInfo(BaseModel):
    """Information escale entre segments."""

    model_config = ConfigDict(extra="forbid")

    airport: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    duration: str


class KayakFlightDTO(BaseModel):
    """Modèle Pydantic d'un vol extrait depuis Kayak."""

    model_config = ConfigDict(extra="forbid")

    price: Annotated[float, Field(gt=0)]
    airline: Annotated[str, Field(min_length=2, max_length=100)]
    departure_time: str
    arrival_time: str
    duration: str
    departure_airport: str | None = None
    arrival_airport: str | None = None
    layovers: list[LayoverInfo] = []
