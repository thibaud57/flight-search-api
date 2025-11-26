"""Routes API FastAPI."""

from logging import Logger
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core import get_logger
from app.core.config import get_settings
from app.models.request import SearchRequest
from app.models.response import HealthResponse, SearchResponse
from app.services import (
    CombinationGenerator,
    CrawlerService,
    GoogleFlightParser,
    ProxyService,
    SearchService,
)

router = APIRouter()


def get_search_service() -> SearchService:
    """Dependency injection pour SearchService."""
    settings = get_settings()
    proxy_service: ProxyService | None = None
    if settings.proxy_config:
        proxy_service = ProxyService(proxy_pool=[settings.proxy_config])
    return SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=CrawlerService(proxy_service=proxy_service),
        flight_parser=GoogleFlightParser(),
    )


@router.get("/health")
def health_check() -> HealthResponse:
    """Retourne le statut sante de l'application."""
    return HealthResponse(status="ok")


@router.post("/api/v1/search-flights", tags=["search"])
async def search_flights_endpoint(
    request: SearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    logger: Annotated[Logger, Depends(get_logger)],
) -> SearchResponse:
    """Endpoint recherche vols multi-city async."""
    logger.info(
        "Flight search started",
        extra={
            "segments_count": len(request.segments_date_ranges),
        },
    )

    response = await search_service.search_flights(request)

    logger.info(
        "Flight search completed",
        extra={
            "segments_count": len(request.segments_date_ranges),
            "search_time_ms": response.search_stats.search_time_ms,
            "total_results": response.search_stats.total_results,
        },
    )

    return response
