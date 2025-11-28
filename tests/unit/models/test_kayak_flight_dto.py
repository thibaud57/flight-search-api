"""Tests pour app/models/kayak_flight_dto.py (KayakFlightDTO, LayoverInfo)."""

import pytest
from pydantic import ValidationError

from app.models import KayakFlightDTO, LayoverInfo

# === LayoverInfo Tests ===


def test_layover_info_creation():
    """Test création LayoverInfo valide."""
    layover = LayoverInfo(airport="JFK", duration="2h 30min")

    assert layover.airport == "JFK"
    assert layover.duration == "2h 30min"


def test_layover_info_required_fields():
    """Test LayoverInfo échoue sans champs requis."""
    with pytest.raises(ValidationError) as exc_info:
        LayoverInfo(airport="JFK")

    assert "duration" in str(exc_info.value)


def test_layover_info_extra_forbid():
    """Test LayoverInfo rejette champs extra."""
    with pytest.raises(ValidationError) as exc_info:
        LayoverInfo(airport="JFK", duration="2h", extra_field="invalid")

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_layover_info_serialization():
    """Test LayoverInfo sérialisation JSON."""
    layover = LayoverInfo(airport="CDG", duration="1h 45min")
    json_data = layover.model_dump()

    assert json_data["airport"] == "CDG"
    assert json_data["duration"] == "1h 45min"


# === KayakFlightDTO Tests ===


def test_kayak_flight_dto_creation(kayak_flight_dto_factory):
    """Test création KayakFlightDTO valide."""
    dto = kayak_flight_dto_factory()

    assert dto.price == 1000.0
    assert dto.airline == "Test Airline"
    assert dto.departure_time == "2026-01-14T10:00:00"
    assert dto.arrival_time == "2026-01-14T20:00:00"
    assert dto.duration == "10h 0min"
    assert dto.departure_airport == "CDG"
    assert dto.arrival_airport == "NRT"
    assert len(dto.layovers) == 0


def test_kayak_flight_dto_custom_values(kayak_flight_dto_factory):
    """Test KayakFlightDTO avec valeurs personnalisées."""
    dto = kayak_flight_dto_factory(
        price=1500.50,
        airline="Air France",
        departure_time="2026-01-15T08:30:00",
        arrival_time="2026-01-15T18:45:00",
        duration="10h 15min",
        departure_airport="ORY",
        arrival_airport="HND",
    )

    assert dto.price == 1500.50
    assert dto.airline == "Air France"
    assert dto.departure_airport == "ORY"
    assert dto.arrival_airport == "HND"


def test_kayak_flight_dto_required_fields():
    """Test KayakFlightDTO échoue sans champs requis."""
    with pytest.raises(ValidationError) as exc_info:
        KayakFlightDTO(price=1000.0)

    error_str = str(exc_info.value)
    assert "airline" in error_str
    assert "departure_time" in error_str
    assert "arrival_time" in error_str
    assert "duration" in error_str


def test_kayak_flight_dto_price_optional():
    """Test KayakFlightDTO accepte price=None (optionnel)."""
    dto = KayakFlightDTO(
        price=None,
        airline="Test",
        departure_time="2026-01-14T10:00:00",
        arrival_time="2026-01-14T20:00:00",
        duration="10h",
    )

    assert dto.price is None
    assert dto.airline == "Test"


def test_kayak_flight_dto_optional_fields():
    """Test KayakFlightDTO champs optionnels (departure/arrival_airport)."""
    dto = KayakFlightDTO(
        price=1000.0,
        airline="Test",
        departure_time="2026-01-14T10:00:00",
        arrival_time="2026-01-14T20:00:00",
        duration="10h",
    )

    assert dto.departure_airport is None
    assert dto.arrival_airport is None
    assert len(dto.layovers) == 0


def test_kayak_flight_dto_with_layovers(kayak_flight_dto_factory):
    """Test KayakFlightDTO avec escales."""
    dto = kayak_flight_dto_factory(num_layovers=2)

    assert len(dto.layovers) == 2
    assert dto.layovers[0].airport == "JF0"
    assert dto.layovers[0].duration == "1h 0min"
    assert dto.layovers[1].airport == "JF1"
    assert dto.layovers[1].duration == "2h 0min"


def test_kayak_flight_dto_extra_forbid():
    """Test KayakFlightDTO rejette champs extra."""
    with pytest.raises(ValidationError) as exc_info:
        KayakFlightDTO(
            price=1000.0,
            airline="Test",
            departure_time="2026-01-14T10:00:00",
            arrival_time="2026-01-14T20:00:00",
            duration="10h",
            extra_field="invalid",
        )

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_kayak_flight_dto_serialization(kayak_flight_dto_factory):
    """Test KayakFlightDTO sérialisation JSON."""
    dto = kayak_flight_dto_factory(price=1234.56, airline="Air France")
    json_data = dto.model_dump()

    assert json_data["price"] == 1234.56
    assert json_data["airline"] == "Air France"
    assert json_data["departure_time"] == "2026-01-14T10:00:00"
    assert "duration" in json_data


def test_kayak_flight_dto_serialization_omits_none():
    """Test KayakFlightDTO sérialisation omet champs None."""
    dto = KayakFlightDTO(
        price=None,
        airline="Test",
        departure_time="2026-01-14T10:00:00",
        arrival_time="2026-01-14T20:00:00",
        duration="10h",
        departure_airport=None,
        arrival_airport=None,
    )
    json_data = dto.model_dump()

    assert "price" not in json_data
    assert "departure_airport" not in json_data
    assert "arrival_airport" not in json_data
    assert json_data["airline"] == "Test"


def test_kayak_flight_dto_deserialization():
    """Test KayakFlightDTO désérialisation depuis dict."""
    data = {
        "price": 999.99,
        "airline": "Lufthansa",
        "departure_time": "2026-01-15T14:30:00",
        "arrival_time": "2026-01-15T22:15:00",
        "duration": "7h 45min",
        "departure_airport": "FRA",
        "arrival_airport": "JFK",
        "layovers": [{"airport": "LHR", "duration": "1h 30min"}],
    }

    dto = KayakFlightDTO(**data)

    assert dto.price == 999.99
    assert dto.airline == "Lufthansa"
    assert len(dto.layovers) == 1
    assert dto.layovers[0].airport == "LHR"


def test_kayak_flight_dto_layovers_default_empty():
    """Test KayakFlightDTO layovers par défaut liste vide."""
    dto = KayakFlightDTO(
        airline="Test",
        departure_time="2026-01-14T10:00:00",
        arrival_time="2026-01-14T20:00:00",
        duration="10h",
    )

    assert dto.layovers == []


def test_kayak_flight_dto_datetime_iso_format():
    """Test KayakFlightDTO accepte format datetime ISO 8601."""
    dto = KayakFlightDTO(
        airline="Test",
        departure_time="2026-12-25T15:30:00",
        arrival_time="2026-12-26T09:45:00",
        duration="18h 15min",
    )

    assert dto.departure_time == "2026-12-25T15:30:00"
    assert dto.arrival_time == "2026-12-26T09:45:00"
