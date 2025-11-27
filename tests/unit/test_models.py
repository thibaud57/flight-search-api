import pytest
from pydantic import ValidationError

from app.models import (
    DateRange,
    FlightCombinationResult,
    SearchRequest,
    SearchResponse,
    SearchStats,
)
from tests.fixtures.helpers import (
    GOOGLE_FLIGHT_TEMPLATE_URL,
    get_date_range,
    get_future_date,
)


def test_date_range_valid_dates(date_range_factory):
    """DateRange dates valides."""
    valid_date_range = date_range_factory(start_offset=1, duration=6, as_dict=True)
    date_range = DateRange(**valid_date_range)

    assert date_range.start == valid_date_range["start"]
    assert date_range.end == valid_date_range["end"]


def test_date_range_end_before_start_fails():
    """End avant start rejetée."""
    start_date, end_date = get_date_range(start_offset=1, duration=6)
    invalid_date_range = {
        "start": end_date.isoformat(),
        "end": start_date.isoformat(),
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


@pytest.mark.parametrize(
    "start,end,description",
    [
        ("2025/06/01", "2025-06-15", "format date invalide"),
        ("2025-02-30", "2025-03-01", "date inexistante"),
    ],
)
def test_date_range_validation_errors(start, end, description):
    """Validation DateRange rejette dates invalides."""
    with pytest.raises(ValidationError):
        DateRange(start=start, end=end)


def test_date_range_future_dates_valid(date_range_factory):
    """Dates très futures acceptées."""
    date_range_data = date_range_factory(start_offset=1825, duration=9, as_dict=True)
    date_range = DateRange(**date_range_data)

    assert date_range.start == date_range_data["start"]
    assert date_range.end == date_range_data["end"]


def test_search_request_valid_two_segments(search_request_factory):
    """Request valide avec 2 segments (minimum)."""
    request = search_request_factory(
        days_segment1=6, days_segment2=5, offset_segment2=7
    )

    assert len(request.segments_date_ranges) == 2


@pytest.mark.parametrize(
    "num_segments,should_fail",
    [
        (1, True),  # minimum 2 segments
        (2, False),  # valid
        (5, False),  # maximum 5 segments
        (6, True),  # too many segments
    ],
)
def test_search_request_segments_count_validation(num_segments, should_fail):
    """Validation nombre segments SearchRequest (2-5)."""
    segments_date_ranges = []
    for i in range(num_segments):
        start = get_future_date(1 + i * 10)
        end = get_future_date(1 + i * 10 + 2)
        segments_date_ranges.append(
            DateRange(start=start.isoformat(), end=end.isoformat())
        )

    if should_fail:
        with pytest.raises(ValidationError):
            SearchRequest(
                template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
                segments_date_ranges=segments_date_ranges,
            )
    else:
        request = SearchRequest(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=segments_date_ranges,
        )
        assert len(request.segments_date_ranges) == num_segments


def test_search_request_empty_segments_fails():
    """Segments vide rejetée."""
    with pytest.raises(ValidationError):
        SearchRequest(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=[],
        )


def test_search_request_explosion_combinatoire_ok():
    """1000 combinaisons exactement accepté."""
    request = SearchRequest(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=get_future_date(1).isoformat(),
                end=get_future_date(10).isoformat(),
            ),
            DateRange(
                start=get_future_date(11).isoformat(),
                end=get_future_date(12).isoformat(),
            ),
            DateRange(
                start=get_future_date(21).isoformat(),
                end=get_future_date(25).isoformat(),
            ),
            DateRange(
                start=get_future_date(31).isoformat(),
                end=get_future_date(32).isoformat(),
            ),
            DateRange(
                start=get_future_date(41).isoformat(),
                end=get_future_date(45).isoformat(),
            ),
        ],
    )

    assert len(request.segments_date_ranges) == 5


def test_search_request_explosion_combinatoire_fails():
    """Plus de 1000 combinaisons rejeté."""
    with pytest.raises(ValidationError) as exc_info:
        SearchRequest(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=[
                DateRange(
                    start=get_future_date(1).isoformat(),
                    end=get_future_date(15).isoformat(),
                ),
                DateRange(
                    start=get_future_date(21).isoformat(),
                    end=get_future_date(35).isoformat(),
                ),
                DateRange(
                    start=get_future_date(41).isoformat(),
                    end=get_future_date(55).isoformat(),
                ),
                DateRange(
                    start=get_future_date(61).isoformat(),
                    end=get_future_date(62).isoformat(),
                ),
                DateRange(
                    start=get_future_date(71).isoformat(),
                    end=get_future_date(72).isoformat(),
                ),
            ],
        )

    assert "Too many combinations" in str(exc_info.value)


def test_search_request_explosion_message_suggests_reduction():
    """Message erreur suggère segment à réduire."""
    with pytest.raises(ValidationError) as exc_info:
        SearchRequest(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=[
                DateRange(
                    start=get_future_date(1).isoformat(),
                    end=get_future_date(10).isoformat(),
                ),
                DateRange(
                    start=get_future_date(21).isoformat(),
                    end=get_future_date(35).isoformat(),
                ),
                DateRange(
                    start=get_future_date(51).isoformat(),
                    end=get_future_date(65).isoformat(),
                ),
            ],
        )
    error_msg = str(exc_info.value)

    assert "date range too large" in error_msg.lower() or "15 days" in error_msg


def test_search_request_asymmetric_ranges_valid():
    """Ranges asymétriques optimisés acceptés."""
    request = SearchRequest(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=get_future_date(1).isoformat(),
                end=get_future_date(15).isoformat(),
            ),
            DateRange(
                start=get_future_date(21).isoformat(),
                end=get_future_date(22).isoformat(),
            ),
            DateRange(
                start=get_future_date(31).isoformat(),
                end=get_future_date(32).isoformat(),
            ),
            DateRange(
                start=get_future_date(41).isoformat(),
                end=get_future_date(42).isoformat(),
            ),
            DateRange(
                start=get_future_date(51).isoformat(),
                end=get_future_date(52).isoformat(),
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
    request = SearchRequest(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=get_future_date(1).isoformat(),
                end=get_future_date(6).isoformat(),
            ),
            DateRange(
                start=get_future_date(11).isoformat(),
                end=get_future_date(15).isoformat(),
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


def test_flight_combination_result_valid_fields(flight_dto_factory, date_range_factory):
    """FlightCombinationResult valide."""
    start_date1, _ = get_date_range(start_offset=1, duration=0)
    start_date2, _ = get_date_range(start_offset=15, duration=0)

    flight = flight_dto_factory(
        price=1250.50,
        airline="Air France",
        departure_time="10:30",
        arrival_time="14:45",
        duration="4h 15min",
        stops=0,
        departure_airport="Aéroport de Paris-Charles de Gaulle",
        arrival_airport="Aéroport international de Tokyo-Haneda",
    )

    combination_data = {
        "segment_dates": [start_date1.isoformat(), start_date2.isoformat()],
        "flights": [
            {
                "price": flight.price,
                "airline": flight.airline,
                "departure_time": flight.departure_time,
                "arrival_time": flight.arrival_time,
                "duration": flight.duration,
                "stops": flight.stops,
                "departure_airport": flight.departure_airport,
                "arrival_airport": flight.arrival_airport,
            }
        ],
    }
    combination = FlightCombinationResult(**combination_data)

    assert len(combination.segment_dates) == 2
    assert combination.segment_dates[0] == start_date1.isoformat()
    assert combination.segment_dates[1] == start_date2.isoformat()
    assert len(combination.flights) == 1
    assert combination.flights[0].price == 1250.50
    assert combination.flights[0].airline == "Air France"


@pytest.mark.parametrize(
    "field,value,description",
    [
        ("price", -100.0, "prix négatif"),
        ("price", 0, "prix zéro"),
        ("airline", "A", "airline trop court"),
        ("stops", -1, "stops négatif"),
    ],
)
def test_google_flight_dto_validation_errors(
    flight_dto_factory, field, value, description
):
    """Validation GoogleFlightDTO rejette valeurs invalides."""
    with pytest.raises(ValidationError):
        flight_dto_factory(**{field: value})


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


def test_search_response_results_sorted_by_price(flight_dto_factory):
    """Results triés prix croissant."""
    start_date1, _ = get_date_range(start_offset=1, duration=0)
    start_date2, _ = get_date_range(start_offset=2, duration=0)

    flight1 = flight_dto_factory(price=2000.0, airline="Airline2")
    flight2 = flight_dto_factory(price=1000.0, airline="Airline1")

    results_unsorted = [
        {
            "segment_dates": [start_date2.isoformat(), start_date2.isoformat()],
            "flights": [
                {
                    "price": flight1.price,
                    "airline": flight1.airline,
                    "departure_time": flight1.departure_time,
                    "arrival_time": flight1.arrival_time,
                    "duration": flight1.duration,
                }
            ],
        },
        {
            "segment_dates": [start_date1.isoformat(), start_date1.isoformat()],
            "flights": [
                {
                    "price": flight2.price,
                    "airline": flight2.airline,
                    "departure_time": flight2.departure_time,
                    "arrival_time": flight2.arrival_time,
                    "duration": flight2.duration,
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


def test_search_response_max_10_results(flight_dto_factory):
    """Max 10 results respecté."""
    start_date1, _ = get_date_range(start_offset=1, duration=0)
    start_date2, _ = get_date_range(start_offset=15, duration=0)

    results = []
    for i in range(11):
        flight = flight_dto_factory(
            price=1000.0 + i * 100,
            airline=f"Airline{i}",
            departure_time="10:00",
            arrival_time="14:00",
            duration="4h",
        )
        results.append(
            {
                "segment_dates": [start_date1.isoformat(), start_date2.isoformat()],
                "flights": [
                    {
                        "price": flight.price,
                        "airline": flight.airline,
                        "departure_time": flight.departure_time,
                        "arrival_time": flight.arrival_time,
                        "duration": flight.duration,
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


def test_flight_time_string_format(flight_dto_factory):
    """GoogleFlightDTO accepte times en format string."""
    flight = flight_dto_factory(
        departure_time="10:30", arrival_time="14:45", duration="4h 15min"
    )

    assert flight.departure_time == "10:30"
    assert flight.arrival_time == "14:45"


def test_flight_duration_format(flight_dto_factory):
    """GoogleFlightDTO duration accepte format string."""
    flight = flight_dto_factory(
        departure_time="10:00", arrival_time="20:30", duration="10h 30min"
    )

    assert flight.duration == "10h 30min"
