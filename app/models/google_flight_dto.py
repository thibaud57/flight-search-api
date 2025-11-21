"""DTO pour données extraites depuis Google Flights."""

from datetime import datetime
from typing import Annotated

import pydantic
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GoogleFlightDTO(BaseModel):
    """Modèle Pydantic d'un vol extrait depuis Google Flights."""

    model_config = ConfigDict(extra="forbid")

    price: Annotated[float, Field(gt=0)]
    airline: Annotated[str, Field(min_length=2, max_length=100)]
    departure_time: datetime
    arrival_time: datetime
    duration: str
    stops: Annotated[int | None, Field(ge=0)] = None
    departure_airport: Annotated[str | None, Field(max_length=10)] = None
    arrival_airport: Annotated[str | None, Field(max_length=10)] = None

    @field_validator("arrival_time", mode="after")
    @classmethod
    def validate_arrival_after_departure(
        cls, v: datetime, info: "pydantic.ValidationInfo"
    ) -> datetime:
        """Valide que arrival_time est après departure_time."""
        departure = info.data.get("departure_time")
        if departure and v <= departure:
            raise ValueError("arrival_time must be after departure_time")
        return v
