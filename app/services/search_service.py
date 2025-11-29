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
    DateRange,
    FlightCombinationResult,
    KayakFlightDTO,
    Provider,
    SearchRequest,
    SearchResponse,
    SearchStats,
)
from app.types import CrawlResultTuple
from app.utils import generate_google_flights_url, generate_kayak_url

if TYPE_CHECKING:
    from app.services.combination_generator import CombinationGenerator
    from app.services.crawler_service import CrawlerService, CrawlResult
    from app.services.filter_service import FilterService
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
        filter_service: FilterService,
    ) -> None:
        """Initialise service avec dependances injectees."""
        self._combination_generator = combination_generator
        self._crawler_service = crawler_service
        self._google_flight_parser = google_flight_parser
        self._kayak_flight_parser = kayak_flight_parser
        self._filter_service = filter_service
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

        combination_results = self._parse_all_results(
            crawl_results, request.segments_date_ranges, provider=provider
        )

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
        if not self._crawler_service.has_valid_cookies():
            logger.error(
                "Cannot start crawling without valid session cookies",
                extra={"provider": provider.value},
            )
            raise RuntimeError(
                f"No valid session cookies for {provider.value}. Call get_session() first."
            )

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
        date_ranges: list[DateRange],
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
                parsed_results, success = self._parse_single_result(
                    combo, result, date_ranges, provider=provider
                )
                combination_results.extend(parsed_results)
                if success:
                    crawls_success += 1
                else:
                    crawls_failed += 1
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

    def _parse_single_result(
        self,
        combo: DateCombination,
        result: CrawlResult,
        date_ranges: list[DateRange],
        *,
        provider: Provider,
    ) -> tuple[list[CombinationResult], bool]:
        """Parse un resultat crawl et retourne (results, success)."""
        if provider == Provider.GOOGLE:
            return self._parse_google_result(combo, result, date_ranges)
        if provider == Provider.KAYAK:
            return self._parse_kayak_result(combo, result, date_ranges)
        raise ValueError(f"Unknown provider: {provider}")

    def _parse_google_result(
        self,
        combo: DateCombination,
        result: CrawlResult,
        date_ranges: list[DateRange],
    ) -> tuple[list[CombinationResult], bool]:
        """Parse resultat Google Flights."""
        flights = self._google_flight_parser.parse(result.html)
        if not flights:
            return [], False

        return [CombinationResult(date_combination=combo, flights=flights)], True

    def _parse_kayak_result(
        self,
        combo: DateCombination,
        result: CrawlResult,
        date_ranges: list[DateRange],
    ) -> tuple[list[CombinationResult], bool]:
        """Parse resultat Kayak et applique filtres si presents."""
        if not result.poll_data:
            return [], False

        all_kayak_results = self._kayak_flight_parser.parse(result.poll_data)
        if not all_kayak_results:
            return [], False

        if self._settings.RANKING_KEEP_ONLY_FIRST_RESULT:
            flights = all_kayak_results[0]
            if not flights:
                return [], False

            filtered_flights = self._apply_filters_to_segments(flights, date_ranges)
            if not filtered_flights:
                return [], False

            return [
                CombinationResult(date_combination=combo, flights=filtered_flights)
            ], True

        results = []
        for result_flights in all_kayak_results:
            if not result_flights:
                continue

            filtered_flights = self._apply_filters_to_segments(
                result_flights, date_ranges
            )

            if filtered_flights:
                results.append(
                    CombinationResult(date_combination=combo, flights=filtered_flights)
                )

        return results, bool(results)

    def _apply_filters_to_segments(
        self,
        flights: list[KayakFlightDTO],
        segment_configs: list[DateRange],
    ) -> list[KayakFlightDTO]:
        """Applique filtres par segment sur liste vols multi-segments."""
        if len(flights) != len(segment_configs):
            logger.warning(
                "Mismatch between flights and segment_configs length",
                extra={
                    "flights_count": len(flights),
                    "segment_configs_count": len(segment_configs),
                },
            )
            return flights

        filtered_flights: list[KayakFlightDTO] = []
        for segment_index, (flight, config) in enumerate(
            zip(flights, segment_configs, strict=False)
        ):
            if config.filters:
                filtered_segment = self._filter_service.apply_filters(
                    [flight], config.filters, segment_index
                )
                if not filtered_segment:
                    return []
                filtered_flights.append(filtered_segment[0])
            else:
                filtered_flights.append(flight)

        return filtered_flights

    def _rank_and_select_top_10(
        self, results: list[CombinationResult]
    ) -> list[CombinationResult]:
        """Trie par prix croissant et selectionne top 10."""
        if not results:
            return []

        sorted_results = sorted(
            results, key=lambda r: r.flights[0].price if r.flights[0].price else 0
        )

        top_results = sorted_results[: self._settings.MAX_RESULTS]

        if top_results:
            best_price = top_results[0].flights[0].price or 0
            logger.info(
                "Ranking completed",
                extra={
                    "best_price": best_price,
                    "total_results": len(top_results),
                },
            )

        return top_results

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
