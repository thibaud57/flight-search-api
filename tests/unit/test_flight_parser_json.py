"""Tests unitaires FlightParser parse_api_responses (network capture JSON)."""

import json

import pytest

from app.exceptions import ParsingError
from app.services.google_flight_parser import GoogleFlightParser


@pytest.fixture
def flight_parser():
    """FlightParser instance."""
    return GoogleFlightParser()


@pytest.fixture
def mock_api_response_three_segments():
    """Mock API response avec 3 segments."""
    json_data = {
        "data": {
            "flights": [
                {
                    "id": "flight_combination_1",
                    "price": {"total": 1250.0, "currency": "EUR"},
                    "segments": [
                        {
                            "segment_index": 0,
                            "departure": {
                                "airport": "CDG",
                                "city": "Paris",
                                "time": "2025-06-01T10:30:00Z",
                            },
                            "arrival": {
                                "airport": "NRT",
                                "city": "Tokyo",
                                "time": "2025-06-02T06:45:00Z",
                            },
                            "carrier": {"name": "Air France", "code": "AF"},
                            "duration_minutes": 765,
                            "stops": 0,
                        },
                        {
                            "segment_index": 1,
                            "departure": {
                                "airport": "NRT",
                                "city": "Tokyo",
                                "time": "2025-06-15T08:00:00Z",
                            },
                            "arrival": {
                                "airport": "KIX",
                                "city": "Kyoto",
                                "time": "2025-06-15T09:30:00Z",
                            },
                            "carrier": {"name": "JAL", "code": "JL"},
                            "duration_minutes": 90,
                            "stops": 0,
                        },
                        {
                            "segment_index": 2,
                            "departure": {
                                "airport": "KIX",
                                "city": "Kyoto",
                                "time": "2025-06-22T14:00:00Z",
                            },
                            "arrival": {
                                "airport": "CDG",
                                "city": "Paris",
                                "time": "2025-06-23T06:30:00Z",
                            },
                            "carrier": {"name": "Lufthansa", "code": "LH"},
                            "duration_minutes": 810,
                            "stops": 1,
                        },
                    ],
                }
            ]
        }
    }

    return {
        "event_type": "response",
        "url": "https://www.google.com/travel/flights/rpc/search",
        "status": 200,
        "resource_type": "xhr",
        "response_data": json.dumps(json_data),
    }


def test_parse_json_three_segments(flight_parser, mock_api_response_three_segments):
    """Parse JSON API avec 3 segments."""
    total_price, flights = flight_parser.parse_api_responses(
        [mock_api_response_three_segments]
    )

    assert total_price == 1250.0
    assert len(flights) == 3

    assert flights[0].airline == "Air France"
    assert flights[0].departure_time == "10:30"
    assert flights[0].arrival_time == "06:45"
    assert flights[0].stops == 0

    assert flights[1].airline == "JAL"
    assert flights[1].departure_time == "08:00"

    assert flights[2].airline == "Lufthansa"
    assert flights[2].stops == 1


def test_parse_json_extracts_total_price(
    flight_parser, mock_api_response_three_segments
):
    """Extraction prix total itinéraire séparé."""
    total_price, flights = flight_parser.parse_api_responses(
        [mock_api_response_three_segments]
    )

    assert total_price == 1250.0

    for flight in flights:
        assert flight.price is None


def test_parse_json_converts_duration(flight_parser, mock_api_response_three_segments):
    """Conversion duration minutes → format display."""
    _, flights = flight_parser.parse_api_responses([mock_api_response_three_segments])

    assert flights[0].duration == "12h 45min"
    assert flights[1].duration == "1h 30min"
    assert flights[2].duration == "13h 30min"


def test_parse_json_invalid_structure(flight_parser):
    """JSON structure invalide lève exception."""
    invalid_response = {
        "event_type": "response",
        "url": "https://www.google.com/travel/flights",
        "status": 200,
        "resource_type": "xhr",
        "response_data": json.dumps({"invalid": "structure"}),
    }

    with pytest.raises(ParsingError):
        flight_parser.parse_api_responses([invalid_response])


def test_parse_json_missing_segment_fields(flight_parser):
    """Champs segment manquants utilisent defaults."""
    json_data = {
        "data": {
            "flights": [
                {
                    "id": "flight_1",
                    "price": {"total": 1000.0},
                    "segments": [
                        {
                            "carrier": {"name": "Air France"},
                            "departure": {"time": "2025-06-01T10:30:00Z"},
                            "arrival": {"time": "2025-06-01T14:00:00Z"},
                        }
                    ],
                }
            ]
        }
    }

    response = {
        "event_type": "response",
        "url": "https://www.google.com/travel/flights",
        "status": 200,
        "resource_type": "xhr",
        "response_data": json.dumps(json_data),
    }

    total_price, flights = flight_parser.parse_api_responses([response])

    assert len(flights) == 1
    assert flights[0].duration == "Unknown"
    assert flights[0].stops == 0


def test_parse_json_missing_total_price(flight_parser):
    """Prix total manquant lève ParsingError."""
    json_data = {
        "data": {
            "flights": [
                {
                    "id": "flight_1",
                    "segments": [
                        {
                            "carrier": {"name": "Air France"},
                            "departure": {"time": "2025-06-01T10:30:00Z"},
                            "arrival": {"time": "2025-06-01T14:00:00Z"},
                        }
                    ],
                }
            ]
        }
    }

    response = {
        "event_type": "response",
        "url": "https://www.google.com/travel/flights",
        "status": 200,
        "resource_type": "xhr",
        "response_data": json.dumps(json_data),
    }

    with pytest.raises(ParsingError):
        flight_parser.parse_api_responses([response])
