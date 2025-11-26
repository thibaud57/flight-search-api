"""Modele KayakSegment avec validation IATA stricte."""

import re

from pydantic import BaseModel, ConfigDict, field_validator


class KayakSegment(BaseModel):
    """Segment de vol Kayak avec validation IATA stricte."""

    model_config = ConfigDict(extra="forbid")

    origin: str
    destination: str
    date: str

    @field_validator("origin", "destination")
    @classmethod
    def validate_iata_code(cls, v: str) -> str:
        """Valide code IATA 3 lettres uppercase."""
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("Code IATA must be 3 uppercase letters")
        return v

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Valide format date YYYY-MM-DD."""
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v
