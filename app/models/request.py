from datetime import date
from typing import Annotated

from pydantic import BaseModel, field_validator, model_validator


class DateRange(BaseModel):
    """Plage de dates pour recherche vols."""

    start: str
    end: str

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Valide le format ISO 8601 des dates."""
        try:
            date.fromisoformat(v)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Invalid date format. Expected ISO 8601 (YYYY-MM-DD)"
            ) from e
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "DateRange":
        """Valide que end > start et start >= aujourd'hui."""
        start_date = date.fromisoformat(self.start)
        end_date = date.fromisoformat(self.end)

        if end_date <= start_date:
            raise ValueError("End date must be after start date")

        if start_date < date.today():
            raise ValueError("Start date must be today or in the future")

        return self


class SearchRequest(BaseModel):
    """Requete de recherche vols multi-destinations."""

    destinations: Annotated[list[str], "Liste destinations (1-5 villes)"]
    date_range: DateRange

    @field_validator("destinations", mode="after")
    @classmethod
    def validate_destinations(cls, v: list[str]) -> list[str]:
        """Valide la liste des destinations."""
        if not v:
            raise ValueError("List should have at least 1 item after validation, not 0")

        if len(v) > 5:
            raise ValueError(
                f"List should have at most 5 items after validation, not {len(v)}"
            )

        cleaned = [dest.strip() for dest in v]

        for dest in cleaned:
            if len(dest) < 2:
                raise ValueError(
                    f"Each destination must have at least 2 characters, got '{dest}'"
                )

        return cleaned
