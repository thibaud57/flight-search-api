"""Models internes du service (non exposés via API)."""

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.google_flight_dto import GoogleFlightDTO
from app.models.kayak_flight_dto import KayakFlightDTO
from app.models.request import validate_iso_date

# Type alias pour supporter Google ET Kayak
FlightDTO = GoogleFlightDTO | KayakFlightDTO


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
    """Resultat intermediaire pour une combinaison dates (avant formatage API)."""

    model_config = ConfigDict(extra="forbid")

    date_combination: DateCombination
    best_flight: FlightDTO
