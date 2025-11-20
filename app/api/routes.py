from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.logger import logger
from app.models.request import SearchRequest
from app.models.response import HealthResponse, SearchResponse
from app.services.search_service import SearchService

router = APIRouter()


def get_search_service() -> SearchService:
    """Dependency injection pour SearchService."""
    return SearchService()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Retourne le statut sante de l'application."""
    return HealthResponse(status="ok")


@router.post("/api/v1/search-flights", response_model=SearchResponse, tags=["search"])
def search_flights_endpoint(
    request: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
) -> SearchResponse:
    """Endpoint recherche vols multi-city (mock Phase 1)."""
    logger.info(
        "Flight search started",
        extra={
            "segments_count": len(request.segments),
        },
    )

    response = search_service.search_flights(request)

    logger.info(
        "Flight search completed",
        extra={
            "segments_count": len(request.segments),
            "search_time_ms": response.search_stats.search_time_ms,
            "total_results": response.search_stats.total_results,
        },
    )

    return response
