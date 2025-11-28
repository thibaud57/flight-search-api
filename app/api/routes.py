"""Routes API FastAPI."""

from logging import Logger
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core import get_logger, get_settings
from app.models import (
    GoogleSearchRequest,
    HealthResponse,
    KayakSearchRequest,
    SearchResponse,
)
from app.services import (
    CombinationGenerator,
    CrawlerService,
    GoogleFlightParser,
    KayakFlightParser,
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
        google_flight_parser=GoogleFlightParser(),
        kayak_flight_parser=KayakFlightParser(),
    )


@router.get("/health")
def health_check() -> HealthResponse:
    """Retourne le statut sante de l'application."""
    return HealthResponse(status="ok")


@router.post("/api/v1/search-google-flights", tags=["search"])
async def search_google_flights_endpoint(
    request: GoogleSearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    logger: Annotated[Logger, Depends(get_logger)],
) -> SearchResponse:
    """Endpoint recherche vols multi-city via Google Flights."""
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


@router.post("/api/v1/search-kayak", tags=["search"])
async def search_kayak_endpoint(
    request: KayakSearchRequest,
    search_service: Annotated[SearchService, Depends(get_search_service)],
    logger: Annotated[Logger, Depends(get_logger)],
) -> SearchResponse:
    """Endpoint recherche vols multi-city via Kayak."""
    logger.info(
        "Kayak search started",
        extra={"segments_count": len(request.segments_date_ranges)},
    )

    response = await search_service.search_flights(request)

    logger.info(
        "Kayak search completed",
        extra={
            "segments_count": len(request.segments_date_ranges),
            "search_time_ms": response.search_stats.search_time_ms,
            "total_results": response.search_stats.total_results,
        },
    )

    return response
