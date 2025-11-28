import pytest
from pydantic import ValidationError

from app.models import FlightCombinationResult


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
