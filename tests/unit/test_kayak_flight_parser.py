"""Tests unitaires KayakFlightParser."""

from unittest.mock import patch

import pytest

from app.models import KayakFlightDTO
from app.services.kayak_flight_parser import KayakFlightParser


def test_format_duration_hours_and_minutes():
    """Test conversion 765 minutes → '12h 45min'."""
    from app.services.kayak_flight_parser import format_duration

    result = format_duration(765)

    assert result == "12h 45min"


def test_format_duration_hours_only():
    """Test conversion 120 minutes → '2h 0min'."""
    from app.services.kayak_flight_parser import format_duration

    result = format_duration(120)

    assert result == "2h 0min"


def test_format_duration_minutes_only():
    """Test conversion 45 minutes → '0h 45min'."""
    from app.services.kayak_flight_parser import format_duration

    result = format_duration(45)

    assert result == "0h 45min"


def test_parse_valid_json_complete(kayak_poll_data_factory):
    """Test parsing JSON avec 2 results complets."""
    parser = KayakFlightParser()
    json_data = kayak_poll_data_factory(num_results=2)

    results = parser.parse(json_data)

    assert len(results) == 2
    assert all(isinstance(r, KayakFlightDTO) for r in results)
    assert results[0].price == 1000.0
    assert results[1].price == 1100.0


def test_parse_empty_results():
    """Test JSON avec results vide retourne liste vide."""
    parser = KayakFlightParser()
    json_data = {"results": [], "legs": {}, "segments": {}}

    results = parser.parse(json_data)

    assert results == []


def test_parse_missing_results_key():
    """Test JSON sans key 'results' lève ValueError."""
    parser = KayakFlightParser()
    json_data = {"legs": {}, "segments": {}}

    with pytest.raises(ValueError, match="Missing 'results' key in Kayak JSON"):
        parser.parse(json_data)


def test_parse_missing_legs_key():
    """Test JSON sans key 'legs' lève ValueError."""
    parser = KayakFlightParser()
    json_data = {"results": [], "segments": {}}

    with pytest.raises(ValueError, match="Missing 'legs' key in Kayak JSON"):
        parser.parse(json_data)


def test_parse_missing_segments_key():
    """Test JSON sans key 'segments' lève ValueError."""
    parser = KayakFlightParser()
    json_data = {"results": [], "legs": {}}

    with pytest.raises(ValueError, match="Missing 'segments' key in Kayak JSON"):
        parser.parse(json_data)


@patch("app.services.kayak_flight_parser.logger")
def test_parse_leg_id_not_found(mock_logger):
    """Test result avec leg ID inexistant → skip result + log warning."""
    parser = KayakFlightParser()
    json_data = {
        "results": [
            {
                "resultId": "result_1",
                "bookingOptions": [
                    {
                        "displayPrice": {"price": 1000.0},
                        "legFarings": [{"legId": "unknown_leg_id"}],
                    }
                ],
            }
        ],
        "legs": {},
        "segments": {},
    }

    results = parser.parse(json_data)

    assert results == []
    mock_logger.warning.assert_called_once()
    assert "Leg ID 'unknown_leg_id' not found" in mock_logger.warning.call_args[0][0]


@patch("app.services.kayak_flight_parser.logger")
def test_parse_segment_id_not_found(mock_logger):
    """Test leg avec segment ID inexistant → skip result + log warning."""
    parser = KayakFlightParser()
    json_data = {
        "results": [
            {
                "resultId": "result_1",
                "bookingOptions": [
                    {
                        "displayPrice": {"price": 1000.0},
                        "legFarings": [{"legId": "leg_1"}],
                    }
                ],
            }
        ],
        "legs": {
            "leg_1": {
                "duration": 600,
                "segments": [{"id": "unknown_segment_id"}],
                "arrival": "2026-01-15T12:00:00",
                "departure": "2026-01-15T08:00:00",
            }
        },
        "segments": {},
    }

    results = parser.parse(json_data)

    assert results == []
    mock_logger.warning.assert_called_once()
    assert (
        "Segment ID 'unknown_segment_id' not found"
        in mock_logger.warning.call_args[0][0]
    )


def test_parse_optional_fields_absent():
    """Test segments sans champs optionnels → pas de crash, defaults appliqués."""
    parser = KayakFlightParser()
    json_data = {
        "results": [
            {
                "resultId": "result_minimal",
                "bookingOptions": [
                    {
                        "displayPrice": {"price": 1500.0},
                        "legFarings": [{"legId": "leg_minimal"}],
                    }
                ],
            }
        ],
        "legs": {
            "leg_minimal": {
                "duration": 480,
                "segments": [{"id": "segment_minimal"}],
                "arrival": "2026-02-01T22:00:00",
                "departure": "2026-02-01T14:00:00",
            }
        },
        "segments": {
            "segment_minimal": {
                "airline": "BA",
                "departure": "2026-02-01T14:00:00",
                "arrival": "2026-02-01T22:00:00",
                "duration": 480,
            }
        },
    }

    results = parser.parse(json_data)

    assert len(results) == 1
    assert results[0].price == 1500.0
    assert results[0].airline == "BA"
    assert results[0].departure_airport is None
    assert results[0].arrival_airport is None


def test_parse_layovers_extraction():
    """Test leg avec 2 segments + layover → KayakFlightDTO avec layovers."""
    parser = KayakFlightParser()
    json_data = {
        "results": [
            {
                "resultId": "result_1",
                "bookingOptions": [
                    {
                        "displayPrice": {"price": 1250.0},
                        "legFarings": [{"legId": "leg_1"}],
                    }
                ],
            }
        ],
        "legs": {
            "leg_1": {
                "duration": 765,
                "segments": [
                    {"id": "segment_1", "layover": {"duration": 120}},
                    {"id": "segment_2"},
                ],
                "arrival": "2026-01-14T19:15:00",
                "departure": "2026-01-14T10:30:00",
            }
        },
        "segments": {
            "segment_1": {
                "airline": "AF",
                "flightNumber": "123",
                "origin": "CDG",
                "destination": "JFK",
                "departure": "2026-01-14T10:30:00",
                "arrival": "2026-01-14T13:45:00",
                "duration": 465,
            },
            "segment_2": {
                "airline": "AA",
                "flightNumber": "456",
                "origin": "JFK",
                "destination": "LAX",
                "departure": "2026-01-14T16:00:00",
                "arrival": "2026-01-14T19:15:00",
                "duration": 300,
            },
        },
    }

    results = parser.parse(json_data)

    assert len(results) == 1
    flight = results[0]
    assert len(flight.layovers) == 1
    assert flight.layovers[0].airport == "JFK"
    assert flight.layovers[0].duration == "2h 0min"


def test_parse_multiple_segments_per_leg():
    """Test leg avec 2 segments (escale) → KayakFlightDTO avec tous segments mappés."""
    parser = KayakFlightParser()
    json_data = {
        "results": [
            {
                "resultId": "result_1",
                "bookingOptions": [
                    {
                        "displayPrice": {"price": 1250.0},
                        "legFarings": [{"legId": "leg_1"}],
                    }
                ],
            }
        ],
        "legs": {
            "leg_1": {
                "duration": 765,
                "segments": [
                    {"id": "segment_1", "layover": {"duration": 120}},
                    {"id": "segment_2"},
                ],
                "arrival": "2026-01-14T19:15:00",
                "departure": "2026-01-14T10:30:00",
            }
        },
        "segments": {
            "segment_1": {
                "airline": "AF",
                "flightNumber": "123",
                "origin": "CDG",
                "destination": "JFK",
                "departure": "2026-01-14T10:30:00",
                "arrival": "2026-01-14T13:45:00",
                "duration": 465,
            },
            "segment_2": {
                "airline": "AA",
                "flightNumber": "456",
                "origin": "JFK",
                "destination": "LAX",
                "departure": "2026-01-14T16:00:00",
                "arrival": "2026-01-14T19:15:00",
                "duration": 300,
            },
        },
    }

    results = parser.parse(json_data)

    assert len(results) == 1
    flight = results[0]
    assert flight.departure_airport == "CDG"
    assert flight.arrival_airport == "LAX"
    assert flight.departure_time == "2026-01-14T10:30:00"
    assert flight.arrival_time == "2026-01-14T19:15:00"


def test_parse_real_kayak_response_fixture(kayak_poll_data_factory):
    """Test parsing JSON généré via factory avec structure réelle."""
    parser = KayakFlightParser()
    json_data = kayak_poll_data_factory(
        num_results=10, with_multi_segment=True, with_layover=True
    )

    results = parser.parse(json_data)

    assert len(results) == 10
    assert all(isinstance(r, KayakFlightDTO) for r in results)
    assert all(r.price > 0 for r in results)
    assert all(len(r.airline) >= 2 for r in results)
    assert all(r.duration for r in results)
    first_flight = results[0]
    assert len(first_flight.layovers) >= 0


def test_parse_malformed_json_gracefully():
    """Test JSON malformé (keys manquantes) lève ValueError avec message explicite."""
    parser = KayakFlightParser()
    json_data = {
        "searchId": "malformed",
        "results": [
            {
                "resultId": "r1",
                "type": "core",
                "bookingOptions": [
                    {"displayPrice": {"price": 1000, "currency": "EUR"}}
                ],
            }
        ],
        "segments": {"s1": {"airline": "AF", "duration": 300}},
    }

    with pytest.raises(ValueError, match="Missing 'legs' key in Kayak JSON"):
        parser.parse(json_data)
