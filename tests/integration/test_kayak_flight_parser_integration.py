"""Tests intégration KayakFlightParser."""

import pytest

from app.services.kayak import KayakFlightParser


class TestKayakFlightParserIntegration:
    """Tests intégration parsing JSON Kayak réel."""

    def test_integration_parse_real_kayak_response(self):
        """Parse JSON réel capturé depuis API Kayak."""
        # Given: JSON réel fixture
        parser = KayakFlightParser()
        json_data = {
            "status": "complete",
            "results": [
                {"resultId": "result_1", "price": 1250.50, "legs": ["leg_1"]},
                {"resultId": "result_2", "price": 980.00, "legs": ["leg_2"]},
            ],
            "legs": {
                "leg_1": {
                    "duration": 765,
                    "stops": 1,
                    "segments": ["segment_1", "segment_2"],
                    "layover": {"duration": 120},
                },
                "leg_2": {"duration": 600, "stops": 0, "segments": ["segment_3"]},
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
                "segment_3": {
                    "airline": "UA",
                    "flightNumber": "789",
                    "origin": "ORD",
                    "destination": "SFO",
                    "departure": "2026-01-15T08:00:00",
                    "arrival": "2026-01-15T12:00:00",
                    "duration": 600,
                },
            },
        }

        # When: Parse JSON
        results = parser.parse(json_data)

        # Then: Vérifications complètes
        assert len(results) == 3
        assert results[0].price == 980.00
        assert results[0].airline == "UA"
        assert results[0].departure_time == "2026-01-15T08:00:00"
        assert results[0].arrival_time == "2026-01-15T12:00:00"
        assert results[0].duration == "10h 0min"
        assert results[0].stops == 0
        assert results[0].departure_airport == "ORD"
        assert results[0].arrival_airport == "SFO"

        assert results[1].price == 1250.50
        assert results[1].airline == "AF"
        assert results[2].price == 1250.50
        assert results[2].airline == "AA"

    def test_integration_parse_malformed_json_gracefully(self):
        """Parse JSON malformé (keys manquantes)."""
        # Given: JSON malformé sans key 'legs'
        parser = KayakFlightParser()
        json_data = {
            "status": "complete",
            "results": [{"resultId": "r1", "price": 1000, "legs": ["l1"]}],
            "segments": {"s1": {"airline": "AF", "duration": 300}},
        }

        # When/Then: Lève ValueError avec message explicite
        with pytest.raises(ValueError, match="Missing 'legs' key in Kayak JSON"):
            parser.parse(json_data)
