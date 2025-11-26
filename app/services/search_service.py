"""Service orchestration recherche vols multi-city."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from app.core import get_settings
from app.exceptions import CaptchaDetectedError, NetworkError, ParsingError
from app.models import (
    CombinationResult,
    DateCombination,
    FlightCombinationResult,
    SearchRequest,
    SearchResponse,
    SearchStats,
)
from app.types import CrawlResultTuple
from app.utils import generate_google_flights_url

if TYPE_CHECKING:
    from app.services.combination_generator import CombinationGenerator
    from app.services.crawler_service import CrawlerService
    from app.services.flight_parser import FlightParser

logger = logging.getLogger(__name__)


class SearchService:
    """Service orchestration recherche vols multi-city."""

    def __init__(
        self,
        combination_generator: CombinationGenerator,
        crawler_service: CrawlerService,
        flight_parser: FlightParser,
    ) -> None:
        """Initialise service avec dependances injectees."""
        self._combination_generator = combination_generator
        self._crawler_service = crawler_service
        self._flight_parser = flight_parser
        self._settings = get_settings()

    async def search_flights(self, request: SearchRequest) -> SearchResponse:
        """Orchestre recherche complete multi-city avec ranking Top 10."""
        start_time = time.time()

        logger.info(
            "Search started",
            extra={"segments_count": len(request.segments_date_ranges)},
        )

        combinations = self._combination_generator.generate_combinations(
            request.segments_date_ranges
        )

        await self._crawler_service.get_google_session()

        crawl_results = await self._crawl_all_combinations(request, combinations)

        combination_results = self._parse_all_results(crawl_results)

        top_results = self._rank_and_select_top_10(combination_results)

        flight_results = self._convert_to_flight_results(top_results)

        search_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Search completed",
            extra={
                "total_results": len(flight_results),
                "search_time_ms": search_time_ms,
            },
        )

        return SearchResponse(
            results=flight_results,
            search_stats=SearchStats(
                total_results=len(flight_results),
                search_time_ms=search_time_ms,
                segments_count=len(request.segments_date_ranges),
            ),
        )

    async def _crawl_all_combinations(
        self,
        request: SearchRequest,
        combinations: list[DateCombination],
    ) -> list[CrawlResultTuple]:
        """Crawle toutes les combinaisons en parallele avec TaskGroup."""
        semaphore = asyncio.Semaphore(self._settings.MAX_CONCURRENCY)
        results: list[CrawlResultTuple] = []

        async def crawl_with_limit(combo: DateCombination) -> None:
            async with semaphore:
                url = self._build_google_flights_url(request, combo)
                try:
                    result = await self._crawler_service.crawl_google_flights(
                        url,
                        use_proxy=True,
                    )
                    results.append((combo, result))
                except (CaptchaDetectedError, NetworkError) as e:
                    logger.warning(
                        "Crawl failed",
                        extra={"url": url, "error": str(e)},
                    )
                    results.append((combo, None))

        async with asyncio.TaskGroup() as tg:
            for combo in combinations:
                tg.create_task(crawl_with_limit(combo))

        return results

    def _build_google_flights_url(
        self, request: SearchRequest, combination: DateCombination
    ) -> str:
        """Genere URL Google Flights en remplacant dates dans template."""
        return generate_google_flights_url(
            request.template_url, combination.segment_dates
        )

    def _parse_all_results(
        self,
        crawl_results: list[CrawlResultTuple],
    ) -> list[CombinationResult]:
        """Parse tous les resultats de crawl."""
        combination_results: list[CombinationResult] = []
        crawls_success = 0
        crawls_failed = 0

        for combo, result in crawl_results:
            if result is None or not result.success:
                crawls_failed += 1
                continue

            try:
                flights = self._flight_parser.parse(result.html)

                if not flights:
                    crawls_failed += 1
                    continue

                combination_results.append(
                    CombinationResult(
                        date_combination=combo,
                        best_flight=flights[0],
                    )
                )
                crawls_success += 1
            except ParsingError as e:
                logger.warning("Parsing failed", extra={"error": str(e)})
                crawls_failed += 1

        logger.info(
            "Crawling completed",
            extra={
                "crawls_success": crawls_success,
                "crawls_failed": crawls_failed,
            },
        )

        return combination_results

    def _rank_and_select_top_10(
        self, results: list[CombinationResult]
    ) -> list[CombinationResult]:
        """Trie par prix croissant et selectionne top 10."""
        if not results:
            return []

        sorted_results = sorted(results, key=lambda r: r.best_flight.price)

        top_10 = sorted_results[:10]

        if top_10:
            logger.info(
                "Ranking completed",
                extra={
                    "top_price_min": top_10[0].best_flight.price,
                    "top_price_max": top_10[-1].best_flight.price
                    if len(top_10) > 1
                    else top_10[0].best_flight.price,
                },
            )

        return top_10

    def _convert_to_flight_results(
        self, combination_results: list[CombinationResult]
    ) -> list[FlightCombinationResult]:
        """Convertit CombinationResult en FlightCombinationResult pour response."""
        return [
            FlightCombinationResult(
                segment_dates=combo_result.date_combination.segment_dates,
                flights=[combo_result.best_flight],
            )
            for combo_result in combination_results
        ]
