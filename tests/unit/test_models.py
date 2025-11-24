from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.models.google_flight_dto import GoogleFlightDTO
from app.models.request import DateRange, SearchRequest
from app.models.response import FlightCombinationResult, SearchResponse, SearchStats
from tests.fixtures.helpers import TEMPLATE_URL


def test_date_range_valid_dates(date_range_factory):
    """DateRange dates valides."""
    valid_date_range = date_range_factory(start_offset=1, duration=6, as_dict=True)
    date_range = DateRange(**valid_date_range)
    assert date_range.start == valid_date_range["start"]
    assert date_range.end == valid_date_range["end"]


def test_date_range_end_before_start_fails():
    """End avant start rejetée."""
    tomorrow = date.today() + timedelta(days=1)
    week_later = tomorrow + timedelta(days=6)
    invalid_date_range = {
        "start": week_later.isoformat(),
        "end": tomorrow.isoformat(),
    }
    with pytest.raises(ValidationError):
        DateRange(**invalid_date_range)


def test_date_range_same_day_valid(date_range_factory):
    """Start = end acceptée (range 1 jour = date exacte)."""
    same_day_range = date_range_factory(start_offset=1, duration=0, as_dict=True)
    date_range = DateRange(**same_day_range)
    assert date_range.start == same_day_range["start"]
    assert date_range.end == same_day_range["end"]


def test_date_range_start_past_fails(date_range_factory):
    """Start dans le passé rejetée."""
    invalid_past_range = date_range_factory(
        start_offset=10, duration=5, past=True, as_dict=True
    )
    with pytest.raises(ValidationError):
        DateRange(**invalid_past_range)


def test_date_range_invalid_format_fails(date_range_factory):
    """Format date invalide rejeté."""
    invalid_format_range = date_range_factory(
        start_offset=1, duration=14, invalid_format=True, as_dict=True
    )
    with pytest.raises(ValidationError):
        DateRange(**invalid_format_range)


def test_date_range_non_existent_date_fails():
    """Date inexistante rejetée."""
    date_range_data = {
        "start": "2025-02-30",
        "end": "2025-03-01",
    }
    with pytest.raises(ValidationError):
        DateRange(**date_range_data)


def test_date_range_future_dates_valid():
    """Dates très futures acceptées."""
    date_range_data = {
        "start": "2030-01-01",
        "end": "2030-01-10",
    }
    date_range = DateRange(**date_range_data)
    assert date_range.start == "2030-01-01"
    assert date_range.end == "2030-01-10"


def test_search_request_valid_two_segments():
    """Request valide avec 2 segments (minimum)."""
    tomorrow = date.today() + timedelta(days=1)
    week_later = tomorrow + timedelta(days=6)

    request = SearchRequest(
        template_url=TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(start=tomorrow.isoformat(), end=week_later.isoformat()),
            DateRange(
                start=(week_later + timedelta(days=1)).isoformat(),
                end=(week_later + timedelta(days=6)).isoformat(),
            ),
        ],
    )
    assert len(request.segments_date_ranges) == 2


def test_search_request_valid_five_segments():
    """Request valide avec 5 segments (maximum)."""
    tomorrow = date.today() + timedelta(days=1)

    segments_date_ranges = []
    for i in range(5):
        start = tomorrow + timedelta(days=i * 10)
        end = start + timedelta(days=2)
        segments_date_ranges.append(
            DateRange(start=start.isoformat(), end=end.isoformat())
        )

    request = SearchRequest(
        template_url=TEMPLATE_URL,
        segments_date_ranges=segments_date_ranges,
    )
    assert len(request.segments_date_ranges) == 5


def test_search_request_single_segment_fails():
    """1 segment rejeté (multi-city minimum 2)."""
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError):
        SearchRequest(
            template_url=TEMPLATE_URL,
            segments_date_ranges=[
                DateRange(
                    start=tomorrow.isoformat(),
                    end=(tomorrow + timedelta(days=5)).isoformat(),
                )
            ],
        )


def test_search_request_too_many_segments_fails():
    """Plus de 5 segments rejetés."""
    tomorrow = date.today() + timedelta(days=1)

    segments_date_ranges = []
    for i in range(6):
        start = tomorrow + timedelta(days=i * 10)
        end = start + timedelta(days=2)
        segments_date_ranges.append(
            DateRange(start=start.isoformat(), end=end.isoformat())
        )

    with pytest.raises(ValidationError):
        SearchRequest(
            template_url=TEMPLATE_URL,
            segments_date_ranges=segments_date_ranges,
        )


def test_search_request_empty_segments_fails():
    """Segments vide rejetée."""
    with pytest.raises(ValidationError):
        SearchRequest(
            template_url=TEMPLATE_URL,
            segments_date_ranges=[],
        )


def test_search_request_explosion_combinatoire_ok():
    """1000 combinaisons exactement accepté."""
    tomorrow = date.today() + timedelta(days=1)

    request = SearchRequest(
        template_url=TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=tomorrow.isoformat(),
                end=(tomorrow + timedelta(days=9)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=10)).isoformat(),
                end=(tomorrow + timedelta(days=11)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=20)).isoformat(),
                end=(tomorrow + timedelta(days=24)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=30)).isoformat(),
                end=(tomorrow + timedelta(days=31)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=40)).isoformat(),
                end=(tomorrow + timedelta(days=44)).isoformat(),
            ),
        ],
    )
    assert len(request.segments_date_ranges) == 5


def test_search_request_explosion_combinatoire_fails():
    """Plus de 1000 combinaisons rejeté."""
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        SearchRequest(
            template_url=TEMPLATE_URL,
            segments_date_ranges=[
                DateRange(
                    start=tomorrow.isoformat(),
                    end=(tomorrow + timedelta(days=14)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=20)).isoformat(),
                    end=(tomorrow + timedelta(days=34)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=40)).isoformat(),
                    end=(tomorrow + timedelta(days=54)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=60)).isoformat(),
                    end=(tomorrow + timedelta(days=61)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=70)).isoformat(),
                    end=(tomorrow + timedelta(days=71)).isoformat(),
                ),
            ],
        )
    assert "Too many combinations" in str(exc_info.value)


def test_search_request_explosion_message_suggests_reduction():
    """Message erreur suggère segment à réduire."""
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(ValidationError) as exc_info:
        SearchRequest(
            template_url=TEMPLATE_URL,
            segments_date_ranges=[
                DateRange(
                    start=tomorrow.isoformat(),
                    end=(tomorrow + timedelta(days=9)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=20)).isoformat(),
                    end=(tomorrow + timedelta(days=34)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=50)).isoformat(),
                    end=(tomorrow + timedelta(days=64)).isoformat(),
                ),
            ],
        )
    error_msg = str(exc_info.value)
    assert "date range too large" in error_msg.lower() or "15 days" in error_msg


def test_search_request_asymmetric_ranges_valid():
    """Ranges asymétriques optimisés acceptés."""
    tomorrow = date.today() + timedelta(days=1)

    request = SearchRequest(
        template_url=TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=tomorrow.isoformat(),
                end=(tomorrow + timedelta(days=14)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=20)).isoformat(),
                end=(tomorrow + timedelta(days=21)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=30)).isoformat(),
                end=(tomorrow + timedelta(days=31)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=40)).isoformat(),
                end=(tomorrow + timedelta(days=41)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=50)).isoformat(),
                end=(tomorrow + timedelta(days=51)).isoformat(),
            ),
        ],
    )
    assert len(request.segments_date_ranges) == 5


def test_search_request_missing_fields_fails():
    """Champs requis manquants."""
    with pytest.raises(ValidationError):
        SearchRequest()


def test_search_request_model_dump_json_valid():
    """Serialization JSON valide."""
    tomorrow = date.today() + timedelta(days=1)

    request = SearchRequest(
        template_url=TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=tomorrow.isoformat(),
                end=(tomorrow + timedelta(days=5)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=10)).isoformat(),
                end=(tomorrow + timedelta(days=14)).isoformat(),
            ),
        ],
    )
    json_str = request.model_dump_json()
    assert json_str is not None
    assert "template_url" in json_str
    assert "google.com/travel/flights" in json_str


def test_search_request_type_hints_pep695_compliant():
    """Type hints code conforme PEP 695."""
    segments_annotation = SearchRequest.model_fields["segments_date_ranges"].annotation

    assert "list" in str(segments_annotation)


def test_flight_combination_result_valid_fields():
    """FlightCombinationResult valide."""
    combination_data = {
        "segment_dates": ["2025-06-01", "2025-06-15"],
        "flights": [
            {
                "price": 1250.50,
                "airline": "Air France",
                "departure_time": "10:30",
                "arrival_time": "14:45",
                "duration": "4h 15min",
                "stops": 0,
                "departure_airport": "Aéroport de Paris-Charles de Gaulle",
                "arrival_airport": "Aéroport international de Tokyo-Haneda",
            }
        ],
    }
    combination = FlightCombinationResult(**combination_data)
    assert len(combination.segment_dates) == 2
    assert combination.segment_dates[0] == "2025-06-01"
    assert combination.segment_dates[1] == "2025-06-15"
    assert len(combination.flights) == 1
    assert combination.flights[0].price == 1250.50
    assert combination.flights[0].airline == "Air France"


def test_google_flight_dto_negative_price_fails():
    """Prix négatif rejeté dans GoogleFlightDTO."""
    with pytest.raises(ValidationError):
        GoogleFlightDTO(
            price=-100.0,
            airline="Air France",
            departure_time="10:30",
            arrival_time="14:00",
            duration="4h",
        )


def test_search_stats_valid_fields():
    """SearchStats valide."""
    stats_data = {
        "total_results": 10,
        "search_time_ms": 50,
        "segments_count": 2,
    }
    stats = SearchStats(**stats_data)
    assert stats.total_results == 10
    assert stats.search_time_ms == 50
    assert stats.segments_count == 2


def test_search_response_results_sorted_by_price():
    """Results triés prix croissant."""
    results_unsorted = [
        {
            "segment_dates": ["2025-06-02", "2025-06-16"],
            "flights": [
                {
                    "price": 2000.0,
                    "airline": "Airline2",
                    "departure_time": "10:00",
                    "arrival_time": "14:00",
                    "duration": "4h",
                }
            ],
        },
        {
            "segment_dates": ["2025-06-01", "2025-06-15"],
            "flights": [
                {
                    "price": 1000.0,
                    "airline": "Airline1",
                    "departure_time": "10:00",
                    "arrival_time": "14:00",
                    "duration": "4h",
                }
            ],
        },
    ]
    stats_data = {
        "total_results": 2,
        "search_time_ms": 50,
        "segments_count": 2,
    }

    with pytest.raises(ValidationError) as exc_info:
        SearchResponse(results=results_unsorted, search_stats=stats_data)
    assert "sorted" in str(exc_info.value).lower()


def test_search_response_max_10_results():
    """Max 10 results respecté."""
    results = []
    for i in range(11):
        results.append(
            {
                "segment_dates": ["2025-06-01", "2025-06-15"],
                "flights": [
                    {
                        "price": 1000.0 + i * 100,
                        "airline": f"Airline{i}",
                        "departure_time": "10:00",
                        "arrival_time": "14:00",
                        "duration": "4h",
                    }
                ],
            }
        )

    stats_data = {
        "total_results": 11,
        "search_time_ms": 50,
        "segments_count": 2,
    }

    with pytest.raises(ValidationError):
        SearchResponse(results=results, search_stats=stats_data)


def test_flight_price_must_be_positive():
    """GoogleFlightDTO price doit être > 0."""
    with pytest.raises(ValidationError):
        GoogleFlightDTO(
            price=0,
            airline="Air France",
            departure_time="10:00",
            arrival_time="14:00",
            duration="4h 00min",
        )


def test_flight_airline_min_length():
    """Airline doit avoir au moins 2 caractères."""
    with pytest.raises(ValidationError):
        GoogleFlightDTO(
            price=100.0,
            airline="A",
            departure_time="10:00",
            arrival_time="14:00",
            duration="4h 00min",
        )


def test_flight_time_string_format():
    """GoogleFlightDTO accepte times en format string."""
    flight = GoogleFlightDTO(
        price=100.0,
        airline="Air France",
        departure_time="10:30",
        arrival_time="14:45",
        duration="4h 15min",
    )
    assert flight.departure_time == "10:30"
    assert flight.arrival_time == "14:45"


def test_flight_duration_format():
    """GoogleFlightDTO duration accepte format string."""
    flight = GoogleFlightDTO(
        price=100.0,
        airline="Air France",
        departure_time="10:00",
        arrival_time="20:30",
        duration="10h 30min",
    )
    assert flight.duration == "10h 30min"


def test_flight_stops_must_be_non_negative():
    """stops doit être >= 0."""
    with pytest.raises(ValidationError):
        GoogleFlightDTO(
            price=100.0,
            airline="Air France",
            departure_time="10:00",
            arrival_time="14:00",
            duration="4h 00min",
            stops=-1,
        )
