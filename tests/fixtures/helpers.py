"""Helper functions pour assertions répétées et utilitaires dates."""

from datetime import date, timedelta

from app.models.google_flight_dto import GoogleFlightDTO
from app.models.response import SearchResponse

# URLs Google Flights pour tests
GOOGLE_FLIGHTS_TEMPLATE_URL = "https://www.google.com/travel/flights?tfs=test"
GOOGLE_FLIGHTS_BASE_URL = "https://www.google.com/travel/flights"
GOOGLE_FLIGHTS_MOCKED_URL = "https://www.google.com/travel/flights?tfs=mocked"

# Alias pour compatibilité (deprecated, utiliser GOOGLE_FLIGHTS_TEMPLATE_URL)
TEMPLATE_URL = GOOGLE_FLIGHTS_TEMPLATE_URL


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


def assert_search_response_valid(response, min_results=0):
    """Helper assertions pour valider SearchResponse structure."""
    assert isinstance(response, SearchResponse)
    assert len(response.results) >= min_results
    assert response.search_stats.total_results >= min_results
    if len(response.results) > 0:
        assert response.results[0].flights[0].price > 0


def assert_results_sorted_by_price(results):
    """Vérifie que results sont triés par prix croissant."""
    for i in range(len(results) - 1):
        current_price = results[i].flights[0].price
        next_price = results[i + 1].flights[0].price
        assert (
            current_price <= next_price
        ), f"Results not sorted: {current_price} > {next_price} at index {i}"


def assert_flight_dto_valid(flight: GoogleFlightDTO):
    """Valide qu'un GoogleFlightDTO a tous les champs requis."""
    assert flight.price > 0, "Price must be positive"
    assert flight.airline, "Airline cannot be empty"
    assert flight.departure_time, "Departure time cannot be empty"
    assert flight.arrival_time, "Arrival time cannot be empty"
    assert flight.duration, "Duration cannot be empty"
    assert flight.stops >= 0, "Stops must be non-negative"
