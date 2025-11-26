"""DTO pour données extraites depuis Google Flights."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class GoogleFlightDTO(BaseModel):
    """Modèle Pydantic d'un vol extrait depuis Google Flights."""

    model_config = ConfigDict(extra="forbid", exclude_none=True)

    price: Annotated[float | None, Field(gt=0)] = None
    airline: Annotated[str, Field(min_length=2, max_length=100)]
    departure_time: str
    arrival_time: str
    duration: str
    stops: Annotated[int | None, Field(ge=0)] = None
    departure_airport: Annotated[str | None, Field(max_length=200)] = None
    arrival_airport: Annotated[str | None, Field(max_length=200)] = None
