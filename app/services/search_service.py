import random
from datetime import date, timedelta

from app.models.request import SearchRequest
from app.models.response import FlightResult, SearchResponse, SearchStats


class SearchService:
    """Service recherche vols (mock Phase 1)."""

    def search_flights(self, request: SearchRequest) -> SearchResponse:
        """Retourne 10 resultats mock tries par prix."""
        mock_data: list[dict[str, float | str | int]] = [
            {
                "price": 825.50,
                "airline": "Air France",
                "days_offset": 0,
            },
            {
                "price": 975.00,
                "airline": "Lufthansa",
                "days_offset": 2,
            },
            {
                "price": 1150.75,
                "airline": "Emirates",
                "days_offset": 4,
            },
            {
                "price": 1320.00,
                "airline": "Delta",
                "days_offset": 6,
            },
            {
                "price": 1485.50,
                "airline": "United",
                "days_offset": 8,
            },
            {
                "price": 1650.00,
                "airline": "British Airways",
                "days_offset": 10,
            },
            {
                "price": 1825.25,
                "airline": "Qatar Airways",
                "days_offset": 12,
            },
            {
                "price": 2010.00,
                "airline": "Singapore Airlines",
                "days_offset": 13,
            },
            {
                "price": 2195.75,
                "airline": "Cathay Pacific",
                "days_offset": 14,
            },
            {
                "price": 2380.50,
                "airline": "ANA",
                "days_offset": 14,
            },
        ]

        start_date = date.fromisoformat(request.date_range.start)
        results = [
            FlightResult(
                price=float(item["price"]),
                airline=str(item["airline"]),
                departure_date=(
                    start_date + timedelta(days=int(item["days_offset"]))
                ).isoformat(),
                route=request.destinations,
            )
            for item in mock_data
        ]

        search_time_ms = random.randint(30, 80)

        search_stats = SearchStats(
            total_results=10,
            search_time_ms=search_time_ms,
            destinations_searched=request.destinations,
        )

        return SearchResponse(results=results, search_stats=search_stats)
