from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Schéma response endpoint health check."""

    status: Literal["ok", "error"]
