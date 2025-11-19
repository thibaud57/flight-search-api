from fastapi import APIRouter

from app.models.response import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Retourne le statut sante de l'application."""
    return HealthResponse(status="ok")
