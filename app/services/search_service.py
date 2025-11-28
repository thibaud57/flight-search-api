"""Service orchestration recherche vols multi-city."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence
from typing import TYPE_CHECKING

from app.core import get_settings
from app.exceptions import CaptchaDetectedError, NetworkError, ParsingError
from app.models import (
    CombinationResult,
    DateCombination,
    FlightCombinationResult,
    FlightDTO,
    Provider,
    SearchRequest,
    SearchResponse,
    SearchStats,
)
from app.types import CrawlResultTuple
from app.utils import generate_google_flights_url, generate_kayak_url

if TYPE_CHECKING:
    from app.services.combination_generator import CombinationGenerator
    from app.services.crawler_service import CrawlerService
    from app.services.google_flight_parser import GoogleFlightParser
    from app.services.kayak_flight_parser import KayakFlightParser

logger = logging.getLogger(__name__)


class SearchService:
    """Service orchestration recherche vols multi-city."""

    def __init__(
        self,
        combination_generator: CombinationGenerator,
        crawler_service: CrawlerService,
        google_flight_parser: GoogleFlightParser,
        kayak_flight_parser: KayakFlightParser,
    ) -> None:
        """Initialise service avec dependances injectees."""
        self._combination_generator = combination_generator
        self._crawler_service = crawler_service
        self._google_flight_parser = google_flight_parser
        self._kayak_flight_parser = kayak_flight_parser
        self._settings = get_settings()

    def _detect_provider(self, url: str) -> Provider:
        """Detecte le provider depuis l'URL."""
        return Provider.GOOGLE if "google" in url else Provider.KAYAK

    async def search_flights(self, request: SearchRequest) -> SearchResponse:
        """Orchestre recherche complete multi-city avec ranking Top 10."""
        start_time = time.time()

        provider = self._detect_provider(request.template_url)

        logger.info(
            "Search started",
            extra={
                "provider": provider.value,
                "segments_count": len(request.segments_date_ranges),
            },
        )

        await self._crawler_service.get_session(provider)

        combinations = self._combination_generator.generate_combinations(
            request.segments_date_ranges
        )

        crawl_results = await self._crawl_all_combinations(
            request, combinations, provider=provider
        )

        combination_results = self._parse_all_results(crawl_results, provider=provider)

        top_results = self._rank_and_select_top_10(combination_results)

        flight_results = self._convert_to_flight_results(top_results)

        search_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Search completed",
            extra={
                "provider": provider.value,
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
        *,
        provider: Provider,
    ) -> list[CrawlResultTuple]:
        """Crawle toutes les combinaisons en parallele avec TaskGroup."""
        semaphore = asyncio.Semaphore(self._settings.MAX_CONCURRENCY)
        results: list[CrawlResultTuple] = []

        async def crawl_with_limit(combo: DateCombination) -> None:
            async with semaphore:
                url = self._build_url(request, combo, provider=provider)
                try:
                    result = await self._crawler_service.crawl_flights(url, provider)
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

    def _build_url(
        self,
        request: SearchRequest,
        combination: DateCombination,
        *,
        provider: Provider,
    ) -> str:
        """Genere URL en remplacant dates dans template."""
        if provider == Provider.GOOGLE:
            return generate_google_flights_url(
                request.template_url, combination.segment_dates
            )
        return generate_kayak_url(request.template_url, combination.segment_dates)

    def _parse_all_results(
        self,
        crawl_results: list[CrawlResultTuple],
        *,
        provider: Provider,
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
                flights: Sequence[FlightDTO]
                if provider == Provider.GOOGLE:
                    flights = self._google_flight_parser.parse(result.html)
                elif provider == Provider.KAYAK:
                    if not result.poll_data:
                        crawls_failed += 1
                        continue
                    all_kayak_results = self._kayak_flight_parser.parse(
                        result.poll_data
                    )
                    if not all_kayak_results:
                        crawls_failed += 1
                        continue
                    flights = all_kayak_results[0]
                else:
                    raise ValueError(f"Unknown provider: {provider}")

                if not flights:
                    crawls_failed += 1
                    continue

                combination_results.append(
                    CombinationResult(
                        date_combination=combo,
                        flights=flights,
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

        sorted_results = sorted(
            results, key=lambda r: r.flights[0].price if r.flights[0].price else 0
        )

        top_10 = sorted_results[:10]

        if top_10:
            best_price = top_10[0].flights[0].price or 0
            logger.info(
                "Ranking completed",
                extra={
                    "best_price": best_price,
                    "total_results": len(top_10),
                },
            )

        return top_10

    def _convert_to_flight_results(
        self, combination_results: list[CombinationResult]
    ) -> list[FlightCombinationResult]:
        """Convertit CombinationResult en FlightCombinationResult pour response."""
        flight_results = []
        for combo_result in combination_results:
            total_price = combo_result.flights[0].price or 0.0
            flights_without_price = [
                flight.model_copy(update={"price": None})
                for flight in combo_result.flights
            ]
            flight_results.append(
                FlightCombinationResult(
                    segment_dates=combo_result.date_combination.segment_dates,
                    total_price=total_price,
                    flights=flights_without_price,
                )
            )
        return flight_results
