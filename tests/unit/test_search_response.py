import pytest
from pydantic import ValidationError

from app.models import SearchResponse


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
        flight_combination_result_factory(base_price=100.0 * (i + 1))
        for i in range(10)
    ]
    stats = search_stats_factory(total_results=10)

    response = SearchResponse(results=results, search_stats=stats)

    assert len(response.results) == 10


def test_search_response_more_than_10_results_fails(
    flight_combination_result_factory, search_stats_factory
):
    """Test SearchResponse échoue si >10 résultats."""
    results = [
        flight_combination_result_factory(base_price=100.0 * (i + 1))
        for i in range(11)
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
