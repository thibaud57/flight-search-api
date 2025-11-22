"""Service orchestration recherche vols multi-city."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import TYPE_CHECKING

from app.exceptions import CaptchaDetectedError, NetworkError, ParsingError
from app.models.request import CombinationResult, DateCombination, SearchRequest
from app.models.response import FlightResult, SearchResponse, SearchStats
from app.utils import generate_google_flights_url

if TYPE_CHECKING:
    from app.services.combination_generator import CombinationGenerator
    from app.services.crawler_service import CrawlerService, CrawlResult
    from app.services.flight_parser import FlightParser

logger = logging.getLogger(__name__)

MAX_CONCURRENCY = 10


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

        logger.info(
            "URLs to crawl",
            extra={"combinations_count": len(combinations)},
        )

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
        self, request: SearchRequest, combinations: list[DateCombination]
    ) -> list[tuple[DateCombination, CrawlResult | None]]:
        """Crawle toutes les combinaisons en parallele."""
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        async def crawl_with_limit(
            combo: DateCombination,
        ) -> tuple[DateCombination, CrawlResult | None]:
            async with semaphore:
                url = self._build_google_flights_url(request, combo)
                logger.info(
                    "Crawling combination",
                    extra={"dates": combo.segment_dates, "url": url},
                )
                try:
                    result = await self._crawler_service.crawl_google_flights(url, use_proxy=True)
                    return (combo, result)
                except (CaptchaDetectedError, NetworkError) as e:
                    logger.warning(
                        "Crawl failed",
                        extra={"url": url, "error": str(e)},
                    )
                    return (combo, None)

        tasks = [crawl_with_limit(combo) for combo in combinations]
        results = await asyncio.gather(*tasks)
        return list(results)

    def _build_google_flights_url(
        self, request: SearchRequest, combination: DateCombination
    ) -> str:
        """Genere URL Google Flights en remplacant dates dans template."""
        return generate_google_flights_url(
            request.template_url, combination.segment_dates
        )

    def _parse_all_results(
        self,
        crawl_results: list[tuple[DateCombination, CrawlResult | None]],
    ) -> list[CombinationResult]:
        """Parse tous les resultats de crawl."""
        logger.info(
            "🔄 [SEARCH] Starting to parse all crawl results",
            extra={"total_crawls": len(crawl_results)},
        )

        combination_results: list[CombinationResult] = []
        crawls_success = 0
        crawls_failed = 0

        for idx, (combo, result) in enumerate(crawl_results):
            logger.info(
                f"📦 [SEARCH] Processing crawl result {idx + 1}/{len(crawl_results)}",
                extra={"dates": combo.segment_dates},
            )

            if result is None or not result.success:
                logger.warning(
                    f"⚠️  [SEARCH] Crawl {idx + 1}: Result is None or failed",
                    extra={"result_is_none": result is None},
                )
                crawls_failed += 1
                continue

            logger.info(
                f"🌐 [SEARCH] Crawl {idx + 1}: HTML received",
                extra={"html_size": len(result.html)},
            )

            try:
                logger.info(f"🔍 [SEARCH] Crawl {idx + 1}: Calling parser...")
                flights = self._flight_parser.parse(result.html)

                logger.info(
                    f"📊 [SEARCH] Crawl {idx + 1}: Parser returned {len(flights)} flights",
                )

                if not flights:
                    logger.warning(f"⚠️  [SEARCH] Crawl {idx + 1}: Zero flights returned")
                    crawls_failed += 1
                    continue

                combination_results.append(
                    CombinationResult(
                        date_combination=combo,
                        best_flight=flights[0],
                    )
                )
                logger.info(
                    f"✅ [SEARCH] Crawl {idx + 1}: Added to results (best price: {flights[0].price}€)",
                )
                crawls_success += 1
            except ParsingError as e:
                logger.warning(
                    f"❌ [SEARCH] Crawl {idx + 1}: Parsing failed",
                    extra={"error": str(e)},
                )
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
    ) -> list[FlightResult]:
        """Convertit CombinationResult en FlightResult pour response."""
        flight_results: list[FlightResult] = []

        for combo_result in combination_results:
            flight_results.append(
                FlightResult(
                    price=combo_result.best_flight.price,
                    airline=combo_result.best_flight.airline,
                    segment_dates=combo_result.date_combination.segment_dates,
                )
            )

        return flight_results

    def _parse_duration(self, duration_str: str) -> int:
        """Parse duration string (ex: '12h 30m') to minutes."""
        if not duration_str:
            return 0

        total_minutes = 0
        hours_match = re.search(r"(\d+)\s*h", duration_str)
        minutes_match = re.search(r"(\d+)\s*m", duration_str)

        if hours_match:
            total_minutes += int(hours_match.group(1)) * 60
        if minutes_match:
            total_minutes += int(minutes_match.group(1))

        return total_minutes
