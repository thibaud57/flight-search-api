"""Tests unitaires FlightParser."""

import pytest

from app.exceptions import ParsingError
from app.services.flight_parser import FlightParser


@pytest.fixture
def parser():
    """Instance FlightParser."""
    return FlightParser()


@pytest.fixture
def valid_flight_html():
    """HTML Google Flights valide avec 10 vols."""
    flights_html = ""
    for i in range(10):
        flights_html += f"""
        <div class="pIav2d">
            <span class="FpEdX">€{100 + i * 50}</span>
            <span class="sSHqwe">Airline {i}</span>
            <time class="departure" datetime="2025-06-01T{10 + i}:00:00">10:{i:02d}</time>
            <time class="arrival" datetime="2025-06-01T{14 + i}:00:00">14:{i:02d}</time>
            <span class="duration">4h 00min</span>
            <span class="stops">Non-stop</span>
            <span class="departure-airport">CDG</span>
            <span class="arrival-airport">NRT</span>
        </div>
        """
    return f"<html><body>{flights_html}</body></html>"


@pytest.fixture
def single_flight_html():
    """HTML avec un seul vol complet."""
    return """
    <html><body>
    <div class="pIav2d">
        <span class="FpEdX">€1250</span>
        <span class="sSHqwe">Air France</span>
        <time class="departure" datetime="2025-06-01T10:30:00">10:30</time>
        <time class="arrival" datetime="2025-06-01T14:45:00">14:45</time>
        <span class="duration">10h 15min</span>
        <span class="stops">1 stop</span>
        <span class="departure-airport">CDG</span>
        <span class="arrival-airport">NRT</span>
    </div>
    </body></html>
    """


def test_parse_valid_html_multiple_flights(parser, valid_flight_html):
    """Test 1: HTML valide avec 10 vols."""
    flights = parser.parse(valid_flight_html)
    assert len(flights) == 10
    for flight in flights:
        assert flight.price > 0
        assert flight.airline is not None


def test_parse_flight_all_fields_present(parser, single_flight_html):
    """Test 2: Vol avec tous champs renseignés."""
    flights = parser.parse(single_flight_html)
    assert len(flights) == 1
    flight = flights[0]
    assert flight.price == 1250.0
    assert flight.airline == "Air France"
    assert flight.departure_time is not None
    assert flight.arrival_time is not None
    assert flight.duration == "10h 15min"
    assert flight.stops == 1
    assert flight.departure_airport == "CDG"
    assert flight.arrival_airport == "NRT"


def test_parse_missing_price(parser, caplog):
    """Test 3: Vol sans prix est skippé."""
    html = """
    <html><body>
    <div class="pIav2d">
        <span class="sSHqwe">Air France</span>
        <time class="departure" datetime="2025-06-01T10:30:00">10:30</time>
        <time class="arrival" datetime="2025-06-01T14:45:00">14:45</time>
        <span class="duration">4h 15min</span>
    </div>
    <div class="pIav2d">
        <span class="FpEdX">€500</span>
        <span class="sSHqwe">Lufthansa</span>
        <time class="departure" datetime="2025-06-01T12:00:00">12:00</time>
        <time class="arrival" datetime="2025-06-01T16:00:00">16:00</time>
        <span class="duration">4h 00min</span>
    </div>
    </body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].airline == "Lufthansa"


def test_parse_invalid_price_format(parser, caplog):
    """Test 4: Prix non numérique est skippé."""
    html = """
    <html><body>
    <div class="pIav2d">
        <span class="FpEdX">N/A</span>
        <span class="sSHqwe">Air France</span>
        <time class="departure" datetime="2025-06-01T10:30:00">10:30</time>
        <time class="arrival" datetime="2025-06-01T14:45:00">14:45</time>
        <span class="duration">4h 15min</span>
    </div>
    <div class="pIav2d">
        <span class="FpEdX">€800</span>
        <span class="sSHqwe">KLM</span>
        <time class="departure" datetime="2025-06-01T14:00:00">14:00</time>
        <time class="arrival" datetime="2025-06-01T18:00:00">18:00</time>
        <span class="duration">4h 00min</span>
    </div>
    </body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].airline == "KLM"


def test_parse_missing_airline(parser, caplog):
    """Test 5: Vol sans compagnie est skippé."""
    html = """
    <html><body>
    <div class="pIav2d">
        <span class="FpEdX">€1000</span>
        <time class="departure" datetime="2025-06-01T10:30:00">10:30</time>
        <time class="arrival" datetime="2025-06-01T14:45:00">14:45</time>
        <span class="duration">4h 15min</span>
    </div>
    <div class="pIav2d">
        <span class="FpEdX">€600</span>
        <span class="sSHqwe">Emirates</span>
        <time class="departure" datetime="2025-06-01T15:00:00">15:00</time>
        <time class="arrival" datetime="2025-06-01T23:00:00">23:00</time>
        <span class="duration">8h 00min</span>
    </div>
    </body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].airline == "Emirates"


def test_parse_invalid_datetime_format(parser):
    """Test 6: Horaire invalide lève ValidationError via skip."""
    html = """
    <html><body>
    <div class="pIav2d">
        <span class="FpEdX">€500</span>
        <span class="sSHqwe">Air France</span>
        <time class="departure" datetime="invalid-date">10:30</time>
        <time class="arrival" datetime="2025-06-01T14:45:00">14:45</time>
        <span class="duration">4h 15min</span>
    </div>
    <div class="pIav2d">
        <span class="FpEdX">€700</span>
        <span class="sSHqwe">British Airways</span>
        <time class="departure" datetime="2025-06-01T08:00:00">08:00</time>
        <time class="arrival" datetime="2025-06-01T12:00:00">12:00</time>
        <span class="duration">4h 00min</span>
    </div>
    </body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].airline == "British Airways"


def test_parse_arrival_before_departure(parser):
    """Test 7: arrival_time < departure_time est skippé."""
    html = """
    <html><body>
    <div class="pIav2d">
        <span class="FpEdX">€500</span>
        <span class="sSHqwe">Air France</span>
        <time class="departure" datetime="2025-06-01T14:00:00">14:00</time>
        <time class="arrival" datetime="2025-06-01T10:00:00">10:00</time>
        <span class="duration">4h 00min</span>
    </div>
    <div class="pIav2d">
        <span class="FpEdX">€900</span>
        <span class="sSHqwe">Swiss</span>
        <time class="departure" datetime="2025-06-01T06:00:00">06:00</time>
        <time class="arrival" datetime="2025-06-01T10:00:00">10:00</time>
        <span class="duration">4h 00min</span>
    </div>
    </body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].airline == "Swiss"


def test_parse_no_flights_found(parser):
    """Test 8: HTML sans .pIav2d lève ParsingError."""
    html = "<html><body><div>No flights here</div></body></html>"
    with pytest.raises(ParsingError) as exc_info:
        parser.parse(html)
    assert "No flights found" in str(exc_info.value)


def test_parse_stops_nonstop(parser):
    """Test 9: Vol direct (Non-stop) → stops=0."""
    html = """
    <html><body>
    <div class="pIav2d">
        <span class="FpEdX">€500</span>
        <span class="sSHqwe">Air France</span>
        <time class="departure" datetime="2025-06-01T10:00:00">10:00</time>
        <time class="arrival" datetime="2025-06-01T14:00:00">14:00</time>
        <span class="duration">4h 00min</span>
        <span class="stops">Non-stop</span>
    </div>
    </body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].stops == 0


def test_parse_stops_multiple(parser):
    """Test 10: Vol avec escales → stops=2."""
    html = """
    <html><body>
    <div class="pIav2d">
        <span class="FpEdX">€500</span>
        <span class="sSHqwe">Air France</span>
        <time class="departure" datetime="2025-06-01T10:00:00">10:00</time>
        <time class="arrival" datetime="2025-06-01T22:00:00">22:00</time>
        <span class="duration">12h 00min</span>
        <span class="stops">2 stops</span>
    </div>
    </body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].stops == 2
