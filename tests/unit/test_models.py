from datetime import date, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models.request import DateRange, FlightSegment, SearchRequest
from app.models.response import Flight, FlightResult, SearchResponse, SearchStats


@pytest.fixture
def valid_date_range():
    """Fixture pour un DateRange valide."""
    tomorrow = date.today() + timedelta(days=1)
    week_later = tomorrow + timedelta(days=6)
    return {
        "start": tomorrow.isoformat(),
        "end": week_later.isoformat(),
    }


@pytest.fixture
def invalid_date_range_end_before_start():
    """Fixture pour un DateRange avec end avant start."""
    tomorrow = date.today() + timedelta(days=1)
    week_later = tomorrow + timedelta(days=6)
    return {
        "start": week_later.isoformat(),
        "end": tomorrow.isoformat(),
    }


@pytest.fixture
def invalid_date_range_past():
    """Fixture pour un DateRange avec start dans le passé."""
    past_date = date.today() - timedelta(days=10)
    past_end = past_date + timedelta(days=5)
    return {
        "start": past_date.isoformat(),
        "end": past_end.isoformat(),
    }


@pytest.fixture
def valid_segment(valid_date_range):
    """Fixture pour un FlightSegment valide."""
    return {
        "from_city": "Paris",
        "to_city": "Tokyo",
        "date_range": valid_date_range,
    }


@pytest.fixture
def invalid_segment_city_too_short(valid_date_range):
    """Fixture pour un FlightSegment avec ville trop courte."""
    return {
        "from_city": "P",
        "to_city": "Tokyo",
        "date_range": valid_date_range,
    }


def test_flight_segment_valid_single_cities(valid_segment):
    """Test 1: Segment valide avec villes uniques."""
    segment = FlightSegment(**valid_segment)
    assert segment.from_city == "Paris"
    assert segment.to_city == "Tokyo"
    assert segment.date_range is not None


def test_flight_segment_valid_multi_airports(valid_date_range):
    """Test 2: Support multi-aéroports séparés virgule."""
    segment_data = {
        "from_city": "Paris,Francfort",
        "to_city": "Tokyo,Osaka",
        "date_range": valid_date_range,
    }
    segment = FlightSegment(**segment_data)
    assert segment.from_city == "Paris,Francfort"
    assert segment.to_city == "Tokyo,Osaka"


def test_flight_segment_city_too_short_fails(invalid_segment_city_too_short):
    """Test 3: Ville 1 caractère rejetée."""
    with pytest.raises(ValidationError):
        FlightSegment(**invalid_segment_city_too_short)


def test_flight_segment_cities_whitespace_trimmed(valid_date_range):
    """Test 4: Villes avec espaces nettoyées."""
    segment_data = {
        "from_city": "  Paris  ",
        "to_city": "Tokyo ",
        "date_range": valid_date_range,
    }
    segment = FlightSegment(**segment_data)
    assert segment.from_city == "Paris"
    assert segment.to_city == "Tokyo"


def test_date_range_valid_dates(valid_date_range):
    """Test 5: DateRange dates valides."""
    date_range = DateRange(**valid_date_range)
    assert date_range.start == valid_date_range["start"]
    assert date_range.end == valid_date_range["end"]


def test_date_range_end_before_start_fails(invalid_date_range_end_before_start):
    """Test 6: End avant start rejetée."""
    with pytest.raises(ValidationError):
        DateRange(**invalid_date_range_end_before_start)


def test_date_range_same_day_valid():
    """Test 7: Start = end acceptée (range 1 jour = date exacte)."""
    tomorrow = date.today() + timedelta(days=1)
    date_range_data = {
        "start": tomorrow.isoformat(),
        "end": tomorrow.isoformat(),
    }
    date_range = DateRange(**date_range_data)
    assert date_range.start == tomorrow.isoformat()
    assert date_range.end == tomorrow.isoformat()


def test_date_range_start_past_fails(invalid_date_range_past):
    """Test 8: Start dans le passé rejetée."""
    with pytest.raises(ValidationError):
        DateRange(**invalid_date_range_past)


def test_date_range_invalid_format_fails():
    """Test 9: Format date invalide rejeté."""
    date_range_data = {
        "start": "01-06-2025",
        "end": "15-06-2025",
    }
    with pytest.raises(ValidationError):
        DateRange(**date_range_data)


def test_date_range_non_existent_date_fails():
    """Test 10: Date inexistante rejetée."""
    date_range_data = {
        "start": "2025-02-30",
        "end": "2025-03-01",
    }
    with pytest.raises(ValidationError):
        DateRange(**date_range_data)


def test_flight_segment_date_range_max_15_days():
    """Test 11: Max 15 jours par segment accepté."""
    tomorrow = date.today() + timedelta(days=1)
    fifteen_days_later = tomorrow + timedelta(days=14)
    segment_data = {
        "from_city": "Paris",
        "to_city": "Tokyo",
        "date_range": {
            "start": tomorrow.isoformat(),
            "end": fifteen_days_later.isoformat(),
        },
    }
    segment = FlightSegment(**segment_data)
    assert segment.date_range is not None


def test_flight_segment_date_range_over_15_days_fails():
    """Test 12: Plus de 15 jours rejeté."""
    tomorrow = date.today() + timedelta(days=1)
    sixteen_days_later = tomorrow + timedelta(days=16)
    segment_data = {
        "from_city": "Paris",
        "to_city": "Tokyo",
        "date_range": {
            "start": tomorrow.isoformat(),
            "end": sixteen_days_later.isoformat(),
        },
    }
    with pytest.raises(ValidationError):
        FlightSegment(**segment_data)


def test_flight_segment_nested_date_range_valid(valid_segment):
    """Test 13: FlightSegment avec DateRange nested."""
    segment = FlightSegment(**valid_segment)
    assert isinstance(segment.date_range, DateRange)
    assert segment.date_range.start is not None
    assert segment.date_range.end is not None


def test_flight_segment_missing_from_city_fails(valid_date_range):
    """Test 14: Champ from_city manquant."""
    segment_data = {
        "to_city": "Tokyo",
        "date_range": valid_date_range,
    }
    with pytest.raises(ValidationError):
        FlightSegment(**segment_data)


def test_date_range_future_dates_valid():
    """Test 15: Dates très futures acceptées."""
    date_range_data = {
        "start": "2030-01-01",
        "end": "2030-01-10",
    }
    date_range = DateRange(**date_range_data)
    assert date_range.start == "2030-01-01"
    assert date_range.end == "2030-01-10"


def test_search_request_valid_two_segments():
    """Test 16: Request valide avec 2 segments (minimum)."""
    tomorrow = date.today() + timedelta(days=1)
    week_later = tomorrow + timedelta(days=6)

    segment1 = {
        "from_city": "Paris",
        "to_city": "Tokyo",
        "date_range": {
            "start": tomorrow.isoformat(),
            "end": week_later.isoformat(),
        },
    }
    segment2 = {
        "from_city": "Tokyo",
        "to_city": "New York",
        "date_range": {
            "start": (week_later + timedelta(days=7)).isoformat(),
            "end": (week_later + timedelta(days=12)).isoformat(),
        },
    }
    request = SearchRequest(segments=[segment1, segment2])
    assert len(request.segments) == 2


def test_search_request_valid_five_segments():
    """Test 17: Request valide avec 5 segments (maximum)."""
    tomorrow = date.today() + timedelta(days=1)

    segments = []
    for i in range(5):
        start = tomorrow + timedelta(days=i * 10)
        end = start + timedelta(days=2)
        segments.append(
            {
                "from_city": f"City{i}",
                "to_city": f"City{i + 1}",
                "date_range": {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                },
            }
        )

    request = SearchRequest(segments=segments)
    assert len(request.segments) == 5


def test_search_request_single_segment_fails():
    """Test 18: 1 segment rejeté (multi-city minimum 2)."""
    tomorrow = date.today() + timedelta(days=1)
    segment = {
        "from_city": "Paris",
        "to_city": "Tokyo",
        "date_range": {
            "start": tomorrow.isoformat(),
            "end": (tomorrow + timedelta(days=5)).isoformat(),
        },
    }
    with pytest.raises(ValidationError):
        SearchRequest(segments=[segment])


def test_search_request_too_many_segments_fails():
    """Test 19: Plus de 5 segments rejetés."""
    tomorrow = date.today() + timedelta(days=1)

    segments = []
    for i in range(6):
        start = tomorrow + timedelta(days=i * 10)
        end = start + timedelta(days=2)
        segments.append(
            {
                "from_city": f"City{i}",
                "to_city": f"City{i + 1}",
                "date_range": {
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                },
            }
        )

    with pytest.raises(ValidationError):
        SearchRequest(segments=segments)


def test_search_request_empty_segments_fails():
    """Test 20: Segments vide rejetée."""
    with pytest.raises(ValidationError):
        SearchRequest(segments=[])


def test_search_request_explosion_combinatoire_ok():
    """Test 21: 1000 combinaisons exactement accepté."""
    tomorrow = date.today() + timedelta(days=1)

    segments = [
        {
            "from_city": "City1",
            "to_city": "City2",
            "date_range": {
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=9)).isoformat(),
            },
        },
        {
            "from_city": "City2",
            "to_city": "City3",
            "date_range": {
                "start": (tomorrow + timedelta(days=10)).isoformat(),
                "end": (tomorrow + timedelta(days=11)).isoformat(),
            },
        },
        {
            "from_city": "City3",
            "to_city": "City4",
            "date_range": {
                "start": (tomorrow + timedelta(days=20)).isoformat(),
                "end": (tomorrow + timedelta(days=24)).isoformat(),
            },
        },
        {
            "from_city": "City4",
            "to_city": "City5",
            "date_range": {
                "start": (tomorrow + timedelta(days=30)).isoformat(),
                "end": (tomorrow + timedelta(days=31)).isoformat(),
            },
        },
        {
            "from_city": "City5",
            "to_city": "City6",
            "date_range": {
                "start": (tomorrow + timedelta(days=40)).isoformat(),
                "end": (tomorrow + timedelta(days=44)).isoformat(),
            },
        },
    ]

    request = SearchRequest(segments=segments)
    assert len(request.segments) == 5


def test_search_request_explosion_combinatoire_fails():
    """Test 22: Plus de 1000 combinaisons rejeté."""
    tomorrow = date.today() + timedelta(days=1)

    segments = [
        {
            "from_city": "City1",
            "to_city": "City2",
            "date_range": {
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=14)).isoformat(),
            },
        },
        {
            "from_city": "City2",
            "to_city": "City3",
            "date_range": {
                "start": (tomorrow + timedelta(days=20)).isoformat(),
                "end": (tomorrow + timedelta(days=34)).isoformat(),
            },
        },
        {
            "from_city": "City3",
            "to_city": "City4",
            "date_range": {
                "start": (tomorrow + timedelta(days=40)).isoformat(),
                "end": (tomorrow + timedelta(days=54)).isoformat(),
            },
        },
        {
            "from_city": "City4",
            "to_city": "City5",
            "date_range": {
                "start": (tomorrow + timedelta(days=60)).isoformat(),
                "end": (tomorrow + timedelta(days=61)).isoformat(),
            },
        },
        {
            "from_city": "City5",
            "to_city": "City6",
            "date_range": {
                "start": (tomorrow + timedelta(days=70)).isoformat(),
                "end": (tomorrow + timedelta(days=71)).isoformat(),
            },
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        SearchRequest(segments=segments)
    assert "Too many combinations" in str(exc_info.value)


def test_search_request_explosion_message_suggests_reduction():
    """Test 23: Message erreur suggère segment à réduire."""
    tomorrow = date.today() + timedelta(days=1)

    segments = [
        {
            "from_city": "City1",
            "to_city": "City2",
            "date_range": {
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=9)).isoformat(),
            },
        },
        {
            "from_city": "City2",
            "to_city": "City3",
            "date_range": {
                "start": (tomorrow + timedelta(days=20)).isoformat(),
                "end": (tomorrow + timedelta(days=34)).isoformat(),
            },
        },
        {
            "from_city": "City3",
            "to_city": "City4",
            "date_range": {
                "start": (tomorrow + timedelta(days=50)).isoformat(),
                "end": (tomorrow + timedelta(days=64)).isoformat(),
            },
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        SearchRequest(segments=segments)
    error_msg = str(exc_info.value)
    assert "Reduce segment" in error_msg
    assert "15 days" in error_msg


def test_search_request_asymmetric_ranges_valid():
    """Test 24: Ranges asymétriques optimisés acceptés."""
    tomorrow = date.today() + timedelta(days=1)

    segments = [
        {
            "from_city": "City1",
            "to_city": "City2",
            "date_range": {
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=14)).isoformat(),
            },
        },
        {
            "from_city": "City2",
            "to_city": "City3",
            "date_range": {
                "start": (tomorrow + timedelta(days=20)).isoformat(),
                "end": (tomorrow + timedelta(days=21)).isoformat(),
            },
        },
        {
            "from_city": "City3",
            "to_city": "City4",
            "date_range": {
                "start": (tomorrow + timedelta(days=30)).isoformat(),
                "end": (tomorrow + timedelta(days=31)).isoformat(),
            },
        },
        {
            "from_city": "City4",
            "to_city": "City5",
            "date_range": {
                "start": (tomorrow + timedelta(days=40)).isoformat(),
                "end": (tomorrow + timedelta(days=41)).isoformat(),
            },
        },
        {
            "from_city": "City5",
            "to_city": "City6",
            "date_range": {
                "start": (tomorrow + timedelta(days=50)).isoformat(),
                "end": (tomorrow + timedelta(days=51)).isoformat(),
            },
        },
    ]

    request = SearchRequest(segments=segments)
    assert len(request.segments) == 5


def test_search_request_missing_segments_fails():
    """Test 25: Champ segments manquant."""
    with pytest.raises(ValidationError):
        SearchRequest()


def test_search_request_model_dump_json_valid():
    """Test 26: Serialization JSON valide."""
    tomorrow = date.today() + timedelta(days=1)

    segments = [
        {
            "from_city": "Paris",
            "to_city": "Tokyo",
            "date_range": {
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=5)).isoformat(),
            },
        },
        {
            "from_city": "Tokyo",
            "to_city": "New York",
            "date_range": {
                "start": (tomorrow + timedelta(days=10)).isoformat(),
                "end": (tomorrow + timedelta(days=14)).isoformat(),
            },
        },
    ]

    request = SearchRequest(segments=segments)
    json_str = request.model_dump_json()
    assert json_str is not None
    assert "Paris" in json_str
    assert "Tokyo" in json_str


def test_search_request_type_hints_pep695_compliant():
    """Test 27: Type hints code conforme PEP 695."""
    segments_annotation = SearchRequest.model_fields["segments"].annotation

    assert "list" in str(segments_annotation)


def test_flight_result_valid_fields():
    """Test 28: FlightResult valide."""
    flight_data = {
        "price": 1250.50,
        "airline": "Air France",
        "departure_date": "2025-06-01",
        "segments": [
            {"from": "Paris", "to": "Tokyo", "date": "2025-06-01"},
            {"from": "Tokyo", "to": "New York", "date": "2025-06-15"},
        ],
    }
    flight = FlightResult(**flight_data)
    assert flight.price == 1250.50
    assert flight.airline == "Air France"
    assert flight.departure_date == "2025-06-01"
    assert len(flight.segments) == 2


def test_flight_result_negative_price_fails():
    """Test 29: Prix négatif rejeté."""
    flight_data = {
        "price": -100.0,
        "airline": "Air France",
        "departure_date": "2025-06-01",
        "segments": [{"from": "Paris", "to": "Tokyo", "date": "2025-06-01"}],
    }
    with pytest.raises(ValidationError):
        FlightResult(**flight_data)


def test_search_stats_valid_fields():
    """Test 30: SearchStats valide."""
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
    """Test 31: Results triés prix croissant."""
    results_unsorted = [
        {
            "price": 2000.0,
            "airline": "Airline2",
            "departure_date": "2025-06-02",
            "segments": [{"from": "A", "to": "B", "date": "2025-06-02"}],
        },
        {
            "price": 1000.0,
            "airline": "Airline1",
            "departure_date": "2025-06-01",
            "segments": [{"from": "A", "to": "B", "date": "2025-06-01"}],
        },
    ]
    stats_data = {
        "total_results": 2,
        "search_time_ms": 50,
        "segments_count": 1,
    }

    with pytest.raises(ValidationError) as exc_info:
        SearchResponse(results=results_unsorted, search_stats=stats_data)
    assert "sorted" in str(exc_info.value).lower()


def test_search_response_max_10_results():
    """Test 32: Max 10 results respecté."""
    results = []
    for i in range(11):
        results.append(
            {
                "price": 1000.0 + i * 100,
                "airline": f"Airline{i}",
                "departure_date": "2025-06-01",
                "segments": [{"from": "A", "to": "B", "date": "2025-06-01"}],
            }
        )

    stats_data = {
        "total_results": 11,
        "search_time_ms": 50,
        "segments_count": 1,
    }

    with pytest.raises(ValidationError):
        SearchResponse(results=results, search_stats=stats_data)


def test_flight_price_must_be_positive():
    """Test 33: Flight price doit être > 0."""
    with pytest.raises(ValidationError):
        Flight(
            price=0,
            airline="Air France",
            departure_time=datetime(2025, 6, 1, 10, 0),
            arrival_time=datetime(2025, 6, 1, 14, 0),
            duration="4h 00min",
        )


def test_flight_airline_min_length():
    """Test 34: Airline doit avoir au moins 2 caractères."""
    with pytest.raises(ValidationError):
        Flight(
            price=100.0,
            airline="A",
            departure_time=datetime(2025, 6, 1, 10, 0),
            arrival_time=datetime(2025, 6, 1, 14, 0),
            duration="4h 00min",
        )


def test_flight_datetime_iso_format():
    """Test 35: Flight accepte datetime valide."""
    flight = Flight(
        price=100.0,
        airline="Air France",
        departure_time=datetime(2025, 6, 1, 10, 30),
        arrival_time=datetime(2025, 6, 1, 14, 45),
        duration="4h 15min",
    )
    assert flight.departure_time == datetime(2025, 6, 1, 10, 30)
    assert flight.arrival_time == datetime(2025, 6, 1, 14, 45)


def test_flight_arrival_must_be_after_departure():
    """Test 36: arrival_time doit être après departure_time."""
    with pytest.raises(ValidationError) as exc_info:
        Flight(
            price=100.0,
            airline="Air France",
            departure_time=datetime(2025, 6, 1, 14, 0),
            arrival_time=datetime(2025, 6, 1, 10, 0),
            duration="4h 00min",
        )
    assert "arrival_time must be after departure_time" in str(exc_info.value)


def test_flight_duration_format():
    """Test 37: Flight duration accepte format string."""
    flight = Flight(
        price=100.0,
        airline="Air France",
        departure_time=datetime(2025, 6, 1, 10, 0),
        arrival_time=datetime(2025, 6, 1, 20, 30),
        duration="10h 30min",
    )
    assert flight.duration == "10h 30min"


def test_flight_stops_must_be_non_negative():
    """Test 38: stops doit être >= 0."""
    with pytest.raises(ValidationError):
        Flight(
            price=100.0,
            airline="Air France",
            departure_time=datetime(2025, 6, 1, 10, 0),
            arrival_time=datetime(2025, 6, 1, 14, 0),
            duration="4h 00min",
            stops=-1,
        )
