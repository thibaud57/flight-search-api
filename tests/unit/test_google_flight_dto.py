import pytest
from pydantic import ValidationError


def test_google_flight_dto_creation(google_flight_dto_factory):
    """Test création GoogleFlightDTO valide."""
    dto = google_flight_dto_factory()

    assert dto.price == 1000.0
    assert dto.airline == "Test Airline"
    assert dto.departure_time == "10:00"
    assert dto.arrival_time == "20:00"
    assert dto.duration == "10h 00min"
    assert dto.stops == 0
    assert dto.departure_airport == "Paris"
    assert dto.arrival_airport == "Tokyo"


def test_google_flight_dto_custom_values(google_flight_dto_factory):
    """Test GoogleFlightDTO avec valeurs personnalisées."""
    dto = google_flight_dto_factory(
        price=1500.50,
        airline="Air France",
        departure_time="08:30",
        arrival_time="18:45",
        duration="10h 15min",
        stops=1,
        departure_airport="CDG",
        arrival_airport="NRT",
    )

    assert dto.price == 1500.50
    assert dto.airline == "Air France"
    assert dto.stops == 1


def test_google_flight_dto_required_fields():
    """Test GoogleFlightDTO échoue sans champs requis."""
    from app.models import GoogleFlightDTO

    with pytest.raises(ValidationError) as exc_info:
        GoogleFlightDTO(
            price=1000.0,
        )

    error_str = str(exc_info.value)
    assert "airline" in error_str
    assert "departure_time" in error_str
    assert "arrival_time" in error_str
    assert "duration" in error_str


def test_google_flight_dto_price_optional(google_flight_dto_factory):
    """Test GoogleFlightDTO accepte price=None (optionnel)."""
    from app.models import GoogleFlightDTO

    dto = GoogleFlightDTO(
        price=None,
        airline="Test",
        departure_time="10:00",
        arrival_time="20:00",
        duration="10h",
    )

    assert dto.price is None
    assert dto.airline == "Test"


def test_google_flight_dto_optional_fields(google_flight_dto_factory):
    """Test GoogleFlightDTO champs optionnels (departure/arrival_airport)."""
    from app.models import GoogleFlightDTO

    dto = GoogleFlightDTO(
        price=1000.0,
        airline="Test",
        departure_time="10:00",
        arrival_time="20:00",
        duration="10h",
        stops=0,
    )

    assert dto.price == 1000.0
    assert dto.stops == 0


def test_google_flight_dto_extra_forbid(google_flight_dto_factory):
    """Test GoogleFlightDTO rejette champs extra."""
    from app.models import GoogleFlightDTO

    with pytest.raises(ValidationError) as exc_info:
        GoogleFlightDTO(
            price=1000.0,
            airline="Test",
            departure_time="10:00",
            arrival_time="20:00",
            duration="10h",
            stops=0,
            extra_field="invalid",
        )

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_google_flight_dto_serialization(google_flight_dto_factory):
    """Test GoogleFlightDTO sérialisation JSON."""
    dto = google_flight_dto_factory(
        price=1234.56,
        airline="Air France",
    )

    json_data = dto.model_dump()

    assert json_data["price"] == 1234.56
    assert json_data["airline"] == "Air France"
    assert json_data["departure_time"] == "10:00"
    assert "duration" in json_data


def test_google_flight_dto_deserialization():
    """Test GoogleFlightDTO désérialisation depuis dict."""
    from app.models import GoogleFlightDTO

    data = {
        "price": 999.99,
        "airline": "Lufthansa",
        "departure_time": "14:30",
        "arrival_time": "22:15",
        "duration": "7h 45min",
        "stops": 1,
        "departure_airport": "FRA",
        "arrival_airport": "JFK",
    }

    dto = GoogleFlightDTO(**data)

    assert dto.price == 999.99
    assert dto.airline == "Lufthansa"
    assert dto.stops == 1


def test_google_flight_dto_stops_optional(google_flight_dto_factory):
    """Test GoogleFlightDTO accepte stops=None (optionnel)."""
    from app.models import GoogleFlightDTO

    dto = GoogleFlightDTO(
        price=1000.0,
        airline="Test",
        departure_time="10:00",
        arrival_time="20:00",
        duration="10h",
        stops=None,
    )

    assert dto.stops is None


def test_google_flight_dto_multiple_stops(google_flight_dto_factory):
    """Test GoogleFlightDTO avec plusieurs escales."""
    dto = google_flight_dto_factory(stops=2)

    assert dto.stops == 2
