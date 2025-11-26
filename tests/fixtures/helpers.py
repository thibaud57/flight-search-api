"""Helper functions pour assertions répétées et utilitaires dates."""

import io
import json
from datetime import date, timedelta
from typing import Any

import pytest

from app.models import FlightCombinationResult, GoogleFlightDTO

# URLs Google Flights pour tests
GOOGLE_FLIGHT_COMPLETE_URL = "https://www.google.com/travel/flights?tfs=CBwQAhooagwIAxIIL20vMDVxdGpyDAgDEggvbS8wN2RmayIKMjAyNS0wNi0wMXIKMjAyNS0wNi0xNXABggELCP___________wFAAUgBmAEB"
GOOGLE_FLIGHT_BASE_URL = "https://www.google.com/travel/flights"

# URL API endpoints pour tests
SEARCH_GOOGLE_FLIGHTS_ENDPOINT = "/api/v1/search-google-flights"
SEARCH_KAYAK_ENDPOINT = "/api/v1/search-kayak"


def get_future_date(days_offset: int = 1) -> date:
    """Retourne date future avec offset depuis aujourd'hui."""
    return date.today() + timedelta(days=days_offset)


def get_past_date(days_offset: int = 1) -> date:
    """Retourne date passée avec offset depuis aujourd'hui."""
    return date.today() - timedelta(days=abs(days_offset))


def get_date_range(
    start_offset: int, duration: int, past: bool = False
) -> tuple[date, date]:
    """Retourne (start_date, end_date) pour range."""
    start = get_past_date(start_offset) if past else get_future_date(start_offset)
    end = start + timedelta(days=duration)
    return start, end


def assert_results_sorted_by_price(results: list[FlightCombinationResult]) -> None:
    """Vérifie que results sont triés par prix croissant."""
    for i in range(len(results) - 1):
        current_price = results[i].flights[0].price
        next_price = results[i + 1].flights[0].price
        assert current_price <= next_price, (
            f"Results not sorted: {current_price} > {next_price} at index {i}"
        )


def assert_flight_dto_valid(flight: GoogleFlightDTO) -> None:
    """Valide qu'un GoogleFlightDTO a tous les champs requis."""
    assert flight.price > 0, "Price must be positive"
    assert flight.airline, "Airline cannot be empty"
    assert flight.departure_time, "Departure time cannot be empty"
    assert flight.arrival_time, "Arrival time cannot be empty"
    assert flight.duration, "Duration cannot be empty"
    assert flight.stops is not None and flight.stops >= 0, "Stops must be non-negative"


def parse_log_output(stream: io.StringIO) -> dict[str, Any]:
    """Parse output stream en dict JSON."""
    output = stream.getvalue()
    try:
        parsed: dict[str, Any] = json.loads(output.strip())
        return parsed
    except json.JSONDecodeError as e:
        pytest.fail(f"Output is not valid JSON: {e}")


def assert_log_contains_fields(parsed_log: dict[str, Any], *fields: str) -> None:
    """Vérifie présence champs requis dans log JSON."""
    for field in fields:
        assert field in parsed_log, f"Missing field: {field}"


def assert_log_field_value(
    parsed_log: dict[str, Any], field: str, expected_value: Any
) -> None:
    """Vérifie valeur exacte champ log."""
    assert parsed_log[field] == expected_value, (
        f"Expected {field}={expected_value}, got {parsed_log.get(field)}"
    )


def assert_log_captured(
    caplog: pytest.LogCaptureFixture, message: str, level: int | None = None
) -> None:
    """Vérifie qu'un log avec message donné a été capturé."""
    matching_records = [
        r
        for r in caplog.records
        if message in r.message and (level is None or r.levelno == level)
    ]
    assert len(matching_records) > 0, (
        f"No log found with message '{message}' (level={level})"
    )


def assert_log_not_captured(
    caplog: pytest.LogCaptureFixture, message: str, level: int | None = None
) -> None:
    """Vérifie qu'aucun log avec message donné n'a été capturé."""
    matching_records = [
        r
        for r in caplog.records
        if message in r.message and (level is None or r.levelno == level)
    ]
    assert len(matching_records) == 0, (
        f"Found {len(matching_records)} log(s) with message '{message}' (level={level})"
    )


def create_date_combinations(num_combinations: int) -> list:
    """Génère liste DateCombination pour tests SearchService."""
    from app.models import DateCombination

    return [
        DateCombination(
            segment_dates=[
                get_future_date(1 + i).isoformat(),
                get_future_date(15 + i).isoformat(),
            ]
        )
        for i in range(num_combinations)
    ]
