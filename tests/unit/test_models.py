from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.models.request import DateRange, SearchRequest
from app.models.response import FlightResult, SearchResponse, SearchStats


@pytest.fixture
def valid_start_date() -> str:
    """Retourne une date de debut valide (demain)."""
    return (date.today() + timedelta(days=1)).isoformat()


@pytest.fixture
def valid_end_date() -> str:
    """Retourne une date de fin valide (dans 15 jours)."""
    return (date.today() + timedelta(days=15)).isoformat()


class TestSearchRequestValidation:
    def test_search_request_valid_single_destination(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        request = SearchRequest(
            destinations=["Paris"],
            date_range=DateRange(start=valid_start_date, end=valid_end_date),
        )
        assert len(request.destinations) == 1
        assert request.destinations[0] == "Paris"

    def test_search_request_valid_two_destinations(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        request = SearchRequest(
            destinations=["Paris", "Tokyo"],
            date_range=DateRange(start=valid_start_date, end=valid_end_date),
        )
        assert len(request.destinations) == 2
        assert request.destinations == ["Paris", "Tokyo"]

    def test_search_request_valid_five_destinations(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        request = SearchRequest(
            destinations=["Paris", "Tokyo", "New York", "London", "Dubai"],
            date_range=DateRange(start=valid_start_date, end=valid_end_date),
        )
        assert len(request.destinations) == 5

    def test_search_request_empty_destinations_fails(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(
                destinations=[],
                date_range=DateRange(start=valid_start_date, end=valid_end_date),
            )
        errors = exc_info.value.errors()
        assert any(
            "at least 1 item" in str(error.get("msg", "")).lower() for error in errors
        )

    def test_search_request_too_many_destinations_fails(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(
                destinations=[
                    "Paris",
                    "Tokyo",
                    "New York",
                    "London",
                    "Dubai",
                    "Berlin",
                ],
                date_range=DateRange(start=valid_start_date, end=valid_end_date),
            )
        errors = exc_info.value.errors()
        assert any(
            "at most 5 items" in str(error.get("msg", "")).lower() for error in errors
        )

    def test_search_request_destination_too_short_fails(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(
                destinations=["P"],
                date_range=DateRange(start=valid_start_date, end=valid_end_date),
            )
        errors = exc_info.value.errors()
        assert any(
            "at least 2 characters" in str(error.get("msg", "")).lower()
            for error in errors
        )

    def test_search_request_destinations_whitespace_trimmed(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        request = SearchRequest(
            destinations=["  Paris  ", "Tokyo "],
            date_range=DateRange(start=valid_start_date, end=valid_end_date),
        )
        assert request.destinations == ["Paris", "Tokyo"]


class TestDateRangeValidation:
    def test_date_range_valid_dates(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        date_range = DateRange(start=valid_start_date, end=valid_end_date)
        assert date_range.start == valid_start_date
        assert date_range.end == valid_end_date

    def test_date_range_end_before_start_fails(self) -> None:
        start = (date.today() + timedelta(days=15)).isoformat()
        end = (date.today() + timedelta(days=1)).isoformat()
        with pytest.raises(ValidationError) as exc_info:
            DateRange(start=start, end=end)
        errors = exc_info.value.errors()
        assert any(
            "end date must be after start date" in str(error.get("msg", "")).lower()
            for error in errors
        )

    def test_date_range_same_day_fails(self) -> None:
        same_date = (date.today() + timedelta(days=1)).isoformat()
        with pytest.raises(ValidationError) as exc_info:
            DateRange(start=same_date, end=same_date)
        errors = exc_info.value.errors()
        assert any(
            "end date must be after start date" in str(error.get("msg", "")).lower()
            for error in errors
        )

    def test_date_range_start_past_fails(self) -> None:
        past_date = (date.today() - timedelta(days=1)).isoformat()
        future_date = (date.today() + timedelta(days=15)).isoformat()
        with pytest.raises(ValidationError) as exc_info:
            DateRange(start=past_date, end=future_date)
        errors = exc_info.value.errors()
        assert any(
            "start date must be today or in the future"
            in str(error.get("msg", "")).lower()
            for error in errors
        )

    def test_date_range_invalid_format_fails(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            DateRange(start="01-06-2025", end="15-06-2025")
        errors = exc_info.value.errors()
        assert any(
            "invalid date format" in str(error.get("msg", "")).lower()
            or "invalid isoformat" in str(error.get("msg", "")).lower()
            for error in errors
        )

    def test_date_range_non_existent_date_fails(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            DateRange(start="2025-02-30", end="2025-03-01")
        errors = exc_info.value.errors()
        assert any("invalid" in str(error.get("msg", "")).lower() for error in errors)

    def test_date_range_future_dates_valid(self) -> None:
        start = "2030-01-01"
        end = "2030-12-31"
        date_range = DateRange(start=start, end=end)
        assert date_range.start == start
        assert date_range.end == end


class TestSearchRequestIntegrity:
    def test_search_request_nested_date_range_valid(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        request = SearchRequest(
            destinations=["Paris"],
            date_range=DateRange(start=valid_start_date, end=valid_end_date),
        )
        assert isinstance(request.date_range, DateRange)
        assert request.date_range.start == valid_start_date

    def test_search_request_missing_destinations_fails(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(
                date_range=DateRange(start=valid_start_date, end=valid_end_date)
            )
        errors = exc_info.value.errors()
        assert any(error.get("loc") == ("destinations",) for error in errors)

    def test_search_request_missing_date_range_fails(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(destinations=["Paris"])
        errors = exc_info.value.errors()
        assert any(error.get("loc") == ("date_range",) for error in errors)

    def test_search_request_destinations_not_list_fails(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SearchRequest(
                destinations="Paris",
                date_range=DateRange(start=valid_start_date, end=valid_end_date),
            )
        errors = exc_info.value.errors()
        assert any("list" in str(error.get("type", "")).lower() for error in errors)

    def test_search_request_model_dump_json_valid(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        request = SearchRequest(
            destinations=["Paris", "Tokyo"],
            date_range=DateRange(start=valid_start_date, end=valid_end_date),
        )
        json_str = request.model_dump_json()
        assert isinstance(json_str, str)
        assert "Paris" in json_str
        assert "Tokyo" in json_str

    def test_search_request_model_validate_from_dict(
        self, valid_start_date: str, valid_end_date: str
    ) -> None:
        data = {
            "destinations": ["Paris"],
            "date_range": {"start": valid_start_date, "end": valid_end_date},
        }
        request = SearchRequest.model_validate(data)
        assert isinstance(request, SearchRequest)
        assert request.destinations == ["Paris"]

    def test_search_request_type_hints_pep695_compliant(self) -> None:
        import inspect

        from app.models.request import SearchRequest

        source = inspect.getsource(SearchRequest)
        assert "list[str]" in source
        assert "List[str]" not in source
        assert "Annotated" in source


class TestFlightResultValidation:
    def test_flight_result_valid_fields(self) -> None:
        flight = FlightResult(
            price=1250.50,
            airline="Air France",
            departure_date="2025-06-01",
            route=["Paris"],
        )
        assert flight.price == 1250.50
        assert flight.airline == "Air France"
        assert flight.departure_date == "2025-06-01"
        assert flight.route == ["Paris"]

    def test_flight_result_negative_price_fails(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            FlightResult(
                price=-100.0,
                airline="Air France",
                departure_date="2025-06-01",
                route=["Paris"],
            )
        errors = exc_info.value.errors()
        assert any(
            "greater than or equal to 0" in str(error.get("msg", "")).lower()
            for error in errors
        )


class TestSearchStatsValidation:
    def test_search_stats_valid_fields(self) -> None:
        stats = SearchStats(
            total_results=10, search_time_ms=50, destinations_searched=["Paris"]
        )
        assert stats.total_results == 10
        assert stats.search_time_ms == 50
        assert stats.destinations_searched == ["Paris"]


class TestSearchResponseValidation:
    def test_search_response_results_sorted_by_price(self) -> None:
        results = [
            FlightResult(
                price=1500.0,
                airline="Lufthansa",
                departure_date="2025-06-05",
                route=["Paris"],
            ),
            FlightResult(
                price=800.0,
                airline="Air France",
                departure_date="2025-06-01",
                route=["Paris"],
            ),
        ]
        stats = SearchStats(
            total_results=2, search_time_ms=50, destinations_searched=["Paris"]
        )

        with pytest.raises(ValidationError) as exc_info:
            SearchResponse(results=results, search_stats=stats)

        errors = exc_info.value.errors()
        assert any(
            "sorted by price" in str(error.get("msg", "")).lower() for error in errors
        )

    def test_search_response_max_10_results(self) -> None:
        results = [
            FlightResult(
                price=float(i * 100),
                airline="Airline",
                departure_date="2025-06-01",
                route=["Paris"],
            )
            for i in range(11)
        ]
        stats = SearchStats(
            total_results=11, search_time_ms=50, destinations_searched=["Paris"]
        )

        with pytest.raises(ValidationError) as exc_info:
            SearchResponse(results=results, search_stats=stats)

        errors = exc_info.value.errors()
        assert any(
            "at most 10 items" in str(error.get("msg", "")).lower() for error in errors
        )
