"""Tests unitaires pour KayakFlightParser."""

import logging

import pytest

from app.services.kayak import KayakFlightParser, format_duration


class TestFormatDuration:
    """Tests conversion durée minutes → string 'Xh Ymin'."""

    def test_format_duration_hours_and_minutes(self):
        """Conversion durée mixte."""
        # Arrange
        minutes = 765

        # Act
        result = format_duration(minutes)

        # Assert
        assert result == "12h 45min"

    def test_format_duration_hours_only(self):
        """Conversion durée ronde."""
        # Arrange
        minutes = 120

        # Act
        result = format_duration(minutes)

        # Assert
        assert result == "2h 0min"

    def test_format_duration_minutes_only(self):
        """Conversion durée < 1h."""
        # Arrange
        minutes = 45

        # Act
        result = format_duration(minutes)

        # Assert
        assert result == "0h 45min"


class TestKayakFlightParser:
    """Tests parsing JSON Kayak → GoogleFlightDTO."""

    def test_parse_valid_json_complete(self):
        """Parse JSON valide complet avec status 'complete'."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {
            "status": "complete",
            "results": [
                {"resultId": "r1", "price": 1250.00, "legs": ["leg1"]},
                {"resultId": "r2", "price": 980.00, "legs": ["leg2"]},
            ],
            "legs": {
                "leg1": {"duration": 765, "stops": 1, "segments": ["seg1"]},
                "leg2": {"duration": 600, "stops": 0, "segments": ["seg2"]},
            },
            "segments": {
                "seg1": {
                    "airline": "AF",
                    "origin": "CDG",
                    "destination": "JFK",
                    "departure": "2026-01-14T10:30:00",
                    "arrival": "2026-01-14T13:45:00",
                    "duration": 465,
                },
                "seg2": {
                    "airline": "UA",
                    "origin": "ORD",
                    "destination": "SFO",
                    "departure": "2026-01-15T08:00:00",
                    "arrival": "2026-01-15T12:00:00",
                    "duration": 600,
                },
            },
        }

        # Act
        results = parser.parse(json_data)

        # Assert
        assert len(results) == 2
        assert results[0].price == 980.00
        assert results[1].price == 1250.00
        assert results[0].airline == "UA"
        assert results[1].airline == "AF"

    def test_parse_empty_results(self):
        """Parse JSON avec results vide."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {"status": "complete", "results": [], "legs": {}, "segments": {}}

        # Act
        results = parser.parse(json_data)

        # Assert
        assert results == []

    def test_parse_missing_results_key(self):
        """JSON sans key 'results'."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {"legs": {}, "segments": {}}

        # Act & Assert
        with pytest.raises(ValueError, match="Missing 'results' key"):
            parser.parse(json_data)

    def test_parse_missing_legs_key(self):
        """JSON sans key 'legs'."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {"results": [], "segments": {}}

        # Act & Assert
        with pytest.raises(ValueError, match="Missing 'legs' key"):
            parser.parse(json_data)

    def test_parse_missing_segments_key(self):
        """JSON sans key 'segments'."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {"results": [], "legs": {}}

        # Act & Assert
        with pytest.raises(ValueError, match="Missing 'segments' key"):
            parser.parse(json_data)

    def test_parse_leg_id_not_found(self, caplog):
        """Result référence leg ID inexistant."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {
            "status": "complete",
            "results": [{"resultId": "r1", "price": 1000, "legs": ["unknown_leg"]}],
            "legs": {},
            "segments": {},
        }

        # Act
        with caplog.at_level(logging.WARNING):
            results = parser.parse(json_data)

        # Assert
        assert results == []
        assert "Leg ID not found" in caplog.text

    def test_parse_segment_id_not_found(self, caplog):
        """Leg référence segment ID inexistant."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {
            "status": "complete",
            "results": [{"resultId": "r1", "price": 1000, "legs": ["leg1"]}],
            "legs": {"leg1": {"duration": 600, "segments": ["unknown_seg"]}},
            "segments": {},
        }

        # Act
        with caplog.at_level(logging.WARNING):
            results = parser.parse(json_data)

        # Assert
        assert results == []
        assert "Segment ID not found" in caplog.text

    def test_parse_optional_fields_absent(self):
        """Segments sans stops/layover."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {
            "status": "complete",
            "results": [{"resultId": "r1", "price": 1500, "legs": ["leg1"]}],
            "legs": {"leg1": {"duration": 480, "segments": ["seg1"]}},
            "segments": {
                "seg1": {
                    "airline": "BA",
                    "departure": "2026-02-01T14:00:00",
                    "arrival": "2026-02-01T22:00:00",
                    "duration": 480,
                }
            },
        }

        # Act
        results = parser.parse(json_data)

        # Assert
        assert len(results) == 1
        assert results[0].stops == 0
        assert results[0].price == 1500
        assert results[0].airline == "BA"

    def test_parse_sorting_by_price(self):
        """Résultats avec prix désordonnés."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {
            "status": "complete",
            "results": [
                {"resultId": "r1", "price": 1500, "legs": ["leg1"]},
                {"resultId": "r2", "price": 1000, "legs": ["leg2"]},
                {"resultId": "r3", "price": 1200, "legs": ["leg3"]},
            ],
            "legs": {
                "leg1": {"duration": 600, "segments": ["seg1"]},
                "leg2": {"duration": 600, "segments": ["seg2"]},
                "leg3": {"duration": 600, "segments": ["seg3"]},
            },
            "segments": {
                "seg1": {
                    "airline": "A1",
                    "departure": "2026-01-01T10:00:00",
                    "arrival": "2026-01-01T20:00:00",
                    "duration": 600,
                },
                "seg2": {
                    "airline": "A2",
                    "departure": "2026-01-01T10:00:00",
                    "arrival": "2026-01-01T20:00:00",
                    "duration": 600,
                },
                "seg3": {
                    "airline": "A3",
                    "departure": "2026-01-01T10:00:00",
                    "arrival": "2026-01-01T20:00:00",
                    "duration": 600,
                },
            },
        }

        # Act
        results = parser.parse(json_data)

        # Assert
        assert len(results) == 3
        assert results[0].price == 1000
        assert results[1].price == 1200
        assert results[2].price == 1500

    def test_parse_multiple_segments_per_leg(self):
        """Leg avec 2+ segments (escales)."""
        # Arrange
        parser = KayakFlightParser()
        json_data = {
            "status": "complete",
            "results": [{"resultId": "r1", "price": 1250, "legs": ["leg1"]}],
            "legs": {"leg1": {"duration": 765, "segments": ["seg1", "seg2"]}},
            "segments": {
                "seg1": {
                    "airline": "AF",
                    "origin": "CDG",
                    "destination": "JFK",
                    "departure": "2026-01-14T10:30:00",
                    "arrival": "2026-01-14T13:45:00",
                    "duration": 465,
                },
                "seg2": {
                    "airline": "AA",
                    "origin": "JFK",
                    "destination": "LAX",
                    "departure": "2026-01-14T16:00:00",
                    "arrival": "2026-01-14T19:15:00",
                    "duration": 300,
                },
            },
        }

        # Act
        results = parser.parse(json_data)

        # Assert
        assert len(results) == 2
        assert results[0].airline == "AF"
        assert results[1].airline == "AA"
        assert results[0].departure_airport == "CDG"
        assert results[1].departure_airport == "JFK"
