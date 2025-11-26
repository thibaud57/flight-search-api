"""Kayak URL Builder et validation segments."""

import re

from pydantic import BaseModel, ConfigDict, field_validator


class KayakSegment(BaseModel):
    """Segment de vol Kayak avec validation IATA."""

    model_config = ConfigDict(extra="forbid")

    origin: str
    destination: str
    date: str

    @field_validator("origin", "destination")
    @classmethod
    def validate_iata_code(cls, v: str) -> str:
        """Valide code IATA 3 lettres uppercase."""
        if not v:
            raise ValueError("Code IATA cannot be empty")
        if len(v) != 3:
            raise ValueError("Code IATA must be exactly 3 characters")
        if not v.isupper():
            raise ValueError("Code IATA must be uppercase")
        if not v.isalpha():
            raise ValueError("Code IATA must contain only letters")
        return v

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Valide format date YYYY-MM-DD."""
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class KayakUrlBuilder:
    """Constructeur d'URLs Kayak multi-city."""

    def __init__(self, base_url: str = "https://www.kayak.fr") -> None:
        """Initialise builder avec URL de base."""
        self.base_url = base_url

    def build_url(self, segments: list[KayakSegment]) -> str:
        """Construit URL Kayak complète depuis segments."""
        if not segments:
            raise ValueError("Segments list cannot be empty")
        if len(segments) > 6:
            raise ValueError("Kayak supports maximum 6 segments")

        segments_path = "/".join(
            f"{seg.origin}-{seg.destination}/{seg.date}" for seg in segments
        )

        return f"{self.base_url}/flights/{segments_path}?sort=bestflight_a"
