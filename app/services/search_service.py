import random
from datetime import date, timedelta

from app.models.request import SearchRequest
from app.models.response import FlightResult, SearchResponse, SearchStats


class SearchService:
    """Service recherche vols multi-city (mock Phase 1)."""

    def search_flights(self, request: SearchRequest) -> SearchResponse:
        """Retourne 10 résultats mock triés par prix."""
        airlines = [
            "Air France",
            "Lufthansa",
            "Emirates",
            "Delta",
            "United",
            "British Airways",
            "Qatar Airways",
            "Singapore Airlines",
            "Cathay Pacific",
            "ANA",
        ]

        base_prices = [
            825.50,
            1050.00,
            1250.00,
            1380.50,
            1520.00,
            1650.75,
            1800.00,
            1950.25,
            2200.00,
            2450.00,
        ]

        results = []
        for i in range(10):
            segments_data = []
            start_date = date.fromisoformat(request.segments[0].date_range.start)

            for j, segment in enumerate(request.segments):
                segment_start = start_date + timedelta(days=j * 7 + i)
                segments_data.append(
                    {
                        "from": segment.from_city,
                        "to": segment.to_city,
                        "date": segment_start.isoformat(),
                    }
                )

            result = FlightResult(
                price=base_prices[i],
                airline=airlines[i],
                departure_date=segments_data[0]["date"],
                segments=segments_data,
            )
            results.append(result)

        search_stats = SearchStats(
            total_results=10,
            search_time_ms=random.randint(30, 80),
            segments_count=len(request.segments),
        )

        return SearchResponse(results=results, search_stats=search_stats)
