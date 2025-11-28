"""Tests pour app/models/response.py (FlightCombinationResult, SearchStats, SearchResponse)."""

import pytest
from pydantic import ValidationError

from app.models import FlightCombinationResult, SearchResponse, SearchStats

# === FlightCombinationResult Tests ===


def test_flight_combination_result_creation(flight_combination_result_factory):
    """Test création FlightCombinationResult valide."""
    result = flight_combination_result_factory()

    assert len(result.flights) == 1
    assert result.total_price >= 800.0
    assert len(result.segment_dates) == 2


def test_flight_combination_result_multiple_flights(
    flight_combination_result_factory,
):
    """Test FlightCombinationResult avec plusieurs vols."""
    result = flight_combination_result_factory(num_flights=3, base_price=500.0)

    assert len(result.flights) == 3
    assert result.total_price == 500.0 + 600.0 + 700.0


def test_flight_combination_result_custom_segment_dates(
    flight_combination_result_factory,
):
    """Test FlightCombinationResult avec dates segments custom."""
    custom_dates = ["2025-06-01", "2025-06-15", "2025-07-01"]
    result = flight_combination_result_factory(segment_dates=custom_dates)

    assert result.segment_dates == custom_dates
    assert len(result.segment_dates) == 3


def test_flight_combination_result_required_fields():
    """Test FlightCombinationResult échoue sans champs requis."""
    with pytest.raises(ValidationError) as exc_info:
        FlightCombinationResult(
            segment_dates=["2025-06-01"],
        )

    error_str = str(exc_info.value)
    assert "flights" in error_str
    assert "total_price" in error_str


def test_flight_combination_result_extra_forbid(flight_combination_result_factory):
    """Test FlightCombinationResult rejette champs extra."""
    result_dict = flight_combination_result_factory().__dict__

    with pytest.raises(ValidationError) as exc_info:
        FlightCombinationResult(**result_dict, extra_field="invalid")

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_flight_combination_result_serialization(flight_combination_result_factory):
    """Test FlightCombinationResult sérialisation JSON."""
    result = flight_combination_result_factory(num_flights=2, base_price=1000.0)

    json_data = result.model_dump()

    assert "segment_dates" in json_data
    assert "flights" in json_data
    assert "total_price" in json_data
    assert json_data["total_price"] == 1000.0 + 1100.0
    assert len(json_data["flights"]) == 2


def test_flight_combination_result_empty_flights_list():
    """Test FlightCombinationResult avec liste vols vide (edge case)."""
    with pytest.raises(ValidationError) as exc_info:
        FlightCombinationResult(
            segment_dates=["2025-06-01", "2025-06-15"],
            flights=[],
            total_price=100.0,
        )

    assert "at least 1 flight required" in str(exc_info.value).lower()


def test_flight_combination_result_null_price_in_flights(google_flight_dto_factory):
    """Test FlightCombinationResult avec prix None dans vols."""
    flight_with_null_price = google_flight_dto_factory(price=None)
    flight_with_price = google_flight_dto_factory(price=800.0)

    result = FlightCombinationResult(
        segment_dates=["2025-06-01", "2025-06-15"],
        flights=[flight_with_null_price, flight_with_price],
        total_price=800.0,
    )

    assert result.total_price == 800.0
    assert len(result.flights) == 2


# === SearchStats Tests ===


def test_search_stats_creation(search_stats_factory):
    """Test création SearchStats valide."""
    stats = search_stats_factory()

    assert stats.total_results == 10
    assert stats.search_time_ms == 100
    assert stats.segments_count == 2


def test_search_stats_custom_values(search_stats_factory):
    """Test SearchStats avec valeurs personnalisées."""
    stats = search_stats_factory(
        total_results=25,
        search_time_ms=250,
        segments_count=3,
    )

    assert stats.total_results == 25
    assert stats.search_time_ms == 250
    assert stats.segments_count == 3


def test_search_stats_zero_results(search_stats_factory):
    """Test SearchStats accepte 0 résultats."""
    stats = search_stats_factory(total_results=0)

    assert stats.total_results == 0


def test_search_stats_required_fields():
    """Test SearchStats échoue sans champs requis."""
    with pytest.raises(ValidationError) as exc_info:
        SearchStats(total_results=10)

    error_str = str(exc_info.value)
    assert "search_time_ms" in error_str
    assert "segments_count" in error_str


def test_search_stats_extra_forbid(search_stats_factory):
    """Test SearchStats rejette champs extra."""
    with pytest.raises(ValidationError) as exc_info:
        SearchStats(
            total_results=10,
            search_time_ms=100,
            segments_count=2,
            extra_field="invalid",
        )

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_search_stats_serialization(search_stats_factory):
    """Test SearchStats sérialisation JSON."""
    stats = search_stats_factory(
        total_results=15,
        search_time_ms=120,
        segments_count=3,
    )

    json_data = stats.model_dump()

    assert json_data == {
        "total_results": 15,
        "search_time_ms": 120,
        "segments_count": 3,
    }


def test_search_stats_deserialization():
    """Test SearchStats désérialisation depuis dict."""
    data = {
        "total_results": 20,
        "search_time_ms": 150,
        "segments_count": 4,
    }

    stats = SearchStats(**data)

    assert stats.total_results == 20
    assert stats.search_time_ms == 150
    assert stats.segments_count == 4


# === SearchResponse Tests ===


def test_search_response_creation(
    flight_combination_result_factory, search_stats_factory
):
    """Test création SearchResponse valide."""
    results = [
        flight_combination_result_factory(base_price=500.0),
        flight_combination_result_factory(base_price=600.0),
        flight_combination_result_factory(base_price=700.0),
    ]
    stats = search_stats_factory(total_results=3, segments_count=2)

    response = SearchResponse(results=results, search_stats=stats)

    assert len(response.results) == 3
    assert response.search_stats.total_results == 3


def test_search_response_max_10_results(
    flight_combination_result_factory, search_stats_factory
):
    """Test SearchResponse valide max 10 résultats."""
    results = [
        flight_combination_result_factory(base_price=100.0 * (i + 1)) for i in range(10)
    ]
    stats = search_stats_factory(total_results=10)

    response = SearchResponse(results=results, search_stats=stats)

    assert len(response.results) == 10


def test_search_response_more_than_10_results_fails(
    flight_combination_result_factory, search_stats_factory
):
    """Test SearchResponse échoue si >10 résultats."""
    results = [
        flight_combination_result_factory(base_price=100.0 * (i + 1)) for i in range(11)
    ]
    stats = search_stats_factory(total_results=11)

    with pytest.raises(ValidationError) as exc_info:
        SearchResponse(results=results, search_stats=stats)

    assert "Maximum 10 results allowed" in str(exc_info.value)


def test_search_response_sorted_ascending(
    flight_combination_result_factory, search_stats_factory
):
    """Test SearchResponse valide ordre croissant prix."""
    results = [
        flight_combination_result_factory(base_price=500.0),
        flight_combination_result_factory(base_price=600.0),
        flight_combination_result_factory(base_price=700.0),
    ]
    stats = search_stats_factory(total_results=3)

    response = SearchResponse(results=results, search_stats=stats)

    assert response.results[0].total_price < response.results[1].total_price
    assert response.results[1].total_price < response.results[2].total_price


def test_search_response_not_sorted_fails(
    flight_combination_result_factory, search_stats_factory
):
    """Test SearchResponse échoue si non trié par prix croissant."""
    results = [
        flight_combination_result_factory(base_price=700.0),
        flight_combination_result_factory(base_price=500.0),
        flight_combination_result_factory(base_price=600.0),
    ]
    stats = search_stats_factory(total_results=3)

    with pytest.raises(ValidationError) as exc_info:
        SearchResponse(results=results, search_stats=stats)

    assert "Results must be sorted by price" in str(exc_info.value)


def test_search_response_empty_results(search_stats_factory):
    """Test SearchResponse accepte résultats vides."""
    stats = search_stats_factory(total_results=0)

    response = SearchResponse(results=[], search_stats=stats)

    assert len(response.results) == 0
    assert response.search_stats.total_results == 0


def test_search_response_required_fields():
    """Test SearchResponse échoue sans champs requis."""
    with pytest.raises(ValidationError) as exc_info:
        SearchResponse(results=[])

    error_str = str(exc_info.value)
    assert "search_stats" in error_str


def test_search_response_extra_forbid(
    flight_combination_result_factory, search_stats_factory
):
    """Test SearchResponse rejette champs extra."""
    results = [flight_combination_result_factory()]
    stats = search_stats_factory()

    with pytest.raises(ValidationError) as exc_info:
        SearchResponse(results=results, search_stats=stats, extra_field="invalid")

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_search_response_serialization(
    flight_combination_result_factory, search_stats_factory
):
    """Test SearchResponse sérialisation JSON."""
    results = [
        flight_combination_result_factory(base_price=1000.0),
        flight_combination_result_factory(base_price=1200.0),
    ]
    stats = search_stats_factory(total_results=2, search_time_ms=150)

    response = SearchResponse(results=results, search_stats=stats)
    json_data = response.model_dump()

    assert "results" in json_data
    assert "search_stats" in json_data
    assert len(json_data["results"]) == 2
    assert json_data["search_stats"]["search_time_ms"] == 150
