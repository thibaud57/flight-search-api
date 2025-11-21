"""Service orchestration recherche vols multi-city."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import TYPE_CHECKING
from urllib.parse import quote

from app.exceptions import CaptchaDetectedError, NetworkError, ParsingError
from app.models.request import CombinationResult, DateCombination, SearchRequest
from app.models.response import FlightResult, SearchResponse, SearchStats

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
            extra={"segments_count": len(request.segments)},
        )

        combinations = self._combination_generator.generate_combinations(
            request.segments
        )

        logger.info(
            "URLs to crawl",
            extra={"combinations_count": len(combinations)},
        )

        crawl_results = await self._crawl_all_combinations(request, combinations)

        combination_results = self._parse_all_results(crawl_results, combinations)

        top_results = self._rank_and_select_top_10(combination_results)

        flight_results = self._convert_to_flight_results(top_results, request)

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
                segments_count=len(request.segments),
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
                try:
                    result = await self._crawler_service.crawl_google_flights(url)
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
        """Construit URL multi-city Google Flights."""
        multi_city_data = []
        for i, segment in enumerate(request.segments):
            multi_city_data.append(
                {
                    "departure_id": segment.from_city,
                    "arrival_id": segment.to_city,
                    "date": combination.segment_dates[i],
                }
            )

        json_str = json.dumps(multi_city_data)
        encoded_json = quote(json_str)

        return f"https://www.google.com/travel/flights?flight_type=3&multi_city_json={encoded_json}&hl=fr&curr=EUR"

    def _parse_all_results(
        self,
        crawl_results: list[tuple[DateCombination, CrawlResult | None]],
        combinations: list[DateCombination],
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
                        flights=flights,
                    )
                )
                crawls_success += 1
            except ParsingError as e:
                logger.warning(
                    "Parsing failed",
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
        """Trie et selectionne top 10 resultats."""
        if not results:
            return []

        def compute_score(r: CombinationResult) -> float:
            return (
                r.total_price * 0.7
                + r.total_duration_minutes * 0.002
                + r.total_stops * 50
            )

        sorted_results = sorted(results, key=compute_score)

        top_10 = sorted_results[:10]

        if top_10:
            logger.info(
                "Ranking completed",
                extra={
                    "top_price_min": top_10[0].total_price,
                    "top_price_max": top_10[-1].total_price
                    if len(top_10) > 1
                    else top_10[0].total_price,
                },
            )

        return top_10

    def _convert_to_flight_results(
        self, combination_results: list[CombinationResult], request: SearchRequest
    ) -> list[FlightResult]:
        """Convertit CombinationResult en FlightResult pour response."""
        flight_results: list[FlightResult] = []

        for combo_result in combination_results:
            segments_data = []
            for i, segment in enumerate(request.segments):
                segments_data.append(
                    {
                        "from": segment.from_city,
                        "to": segment.to_city,
                        "date": combo_result.date_combination.segment_dates[i],
                    }
                )

            airlines = list({f.airline for f in combo_result.flights})
            airline_str = airlines[0] if len(airlines) == 1 else "Mixed"

            flight_results.append(
                FlightResult(
                    price=combo_result.total_price,
                    airline=airline_str,
                    departure_date=combo_result.date_combination.segment_dates[0],
                    segments=segments_data,
                )
            )

        return flight_results
