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
        price = 100 + i * 50
        airline = f"Airline {i}"
        flights_html += f"""
        <li class="pIav2d">
            <div aria-label="À partir de {price} euros. Départ de Paris à 10:{i:02d}, arrivée à Tokyo à 14:{i:02d}. Durée totale : 4 h 00 min. Vol direct avec {airline}."></div>
        </li>
        """
    return f"<html><body><ul>{flights_html}</ul></body></html>"


@pytest.fixture
def single_flight_html():
    """HTML avec un seul vol complet."""
    return """
    <html><body>
    <ul>
    <li class="pIav2d">
        <div aria-label="À partir de 1250 euros. Départ de Paris à 10:30, arrivée à Tokyo à 14:45. Durée totale : 10h 15min. 1 escale avec Air France."></div>
    </li>
    </ul>
    </body></html>
    """


def test_parse_valid_html_multiple_flights(parser, valid_flight_html):
    """HTML valide avec 10 vols."""
    flights = parser.parse(valid_flight_html)
    assert len(flights) == 10
    for flight in flights:
        assert flight.price > 0
        assert flight.airline is not None


def test_parse_flight_all_fields_present(parser, single_flight_html):
    """Vol avec tous champs renseignés."""
    flights = parser.parse(single_flight_html)
    assert len(flights) == 1
    flight = flights[0]
    assert flight.price == 1250.0
    assert flight.airline == "Air France"
    assert flight.departure_time == "10:30"
    assert flight.arrival_time == "14:45"
    assert flight.duration == "10h 15min"
    assert flight.stops == 1
    assert flight.departure_airport == "Paris"
    assert flight.arrival_airport == "Tokyo"


def test_parse_price_with_spaces(parser):
    """Prix avec espaces '1 270 euros' → 1270.0."""
    html = """
    <html><body><ul>
    <li class="pIav2d">
        <div aria-label="À partir de 1 270 euros. Départ de Paris à 10:30, arrivée à Tokyo à 14:45. Durée totale : 10h 15min. Vol direct avec Air France."></div>
    </li>
    </ul></body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].price == 1270.0
    assert flights[0].airline == "Air France"


def test_parse_missing_price(parser, caplog):
    """Vol sans prix est skippé."""
    html = """
    <html><body><ul>
    <li class="pIav2d">
        <div aria-label="Départ de Paris à 10:30, arrivée à Tokyo à 14:45. Durée totale : 4h 15min. Vol direct avec Air France."></div>
    </li>
    <li class="pIav2d">
        <div aria-label="À partir de 500 euros. Départ de Paris à 12:00, arrivée à Tokyo à 16:00. Durée totale : 4h 00min. Vol direct avec Lufthansa."></div>
    </li>
    </ul></body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].airline == "Lufthansa"


def test_parse_invalid_price_format(parser, caplog):
    """Prix non numérique est skippé."""
    html = """
    <html><body><ul>
    <li class="pIav2d">
        <div aria-label="À partir de N/A euros. Départ de Paris à 10:30, arrivée à Tokyo à 14:45. Durée totale : 4h 15min. Vol direct avec Air France."></div>
    </li>
    <li class="pIav2d">
        <div aria-label="À partir de 800 euros. Départ de Paris à 14:00, arrivée à Tokyo à 18:00. Durée totale : 4h 00min. Vol direct avec KLM."></div>
    </li>
    </ul></body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].airline == "KLM"


def test_parse_missing_airline(parser, caplog):
    """Vol sans compagnie est skippé."""
    html = """
    <html><body><ul>
    <li class="pIav2d">
        <div aria-label="À partir de 1000 euros. Départ de Paris à 10:30, arrivée à Tokyo à 14:45. Durée totale : 4h 15min. Vol direct."></div>
    </li>
    <li class="pIav2d">
        <div aria-label="À partir de 600 euros. Départ de Paris à 15:00, arrivée à Tokyo à 23:00. Durée totale : 8h 00min. Vol direct avec Emirates."></div>
    </li>
    </ul></body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].airline == "Emirates"


def test_parse_invalid_datetime_format(parser):
    """Horaire invalide est skippé si regex ne match pas."""
    html = """
    <html><body><ul>
    <li class="pIav2d">
        <div aria-label="À partir de 500 euros. Départ de Paris sans heure, arrivée à Tokyo sans heure. Durée totale : 4h 15min. Vol direct avec Air France."></div>
    </li>
    <li class="pIav2d">
        <div aria-label="À partir de 700 euros. Départ de Paris à 08:00, arrivée à Tokyo à 12:00. Durée totale : 4h 00min. Vol direct avec British Airways."></div>
    </li>
    </ul></body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].airline == "British Airways"


def test_parse_arrival_before_departure(parser):
    """arrival_time < departure_time accepté (pas de validation temporelle)."""
    html = """
    <html><body><ul>
    <li class="pIav2d">
        <div aria-label="À partir de 500 euros. Départ de Paris à 14:00, arrivée à Tokyo à 10:00. Durée totale : 4h 00min. Vol direct avec Air France."></div>
    </li>
    <li class="pIav2d">
        <div aria-label="À partir de 900 euros. Départ de Paris à 06:00, arrivée à Tokyo à 10:00. Durée totale : 4h 00min. Vol direct avec Swiss."></div>
    </li>
    </ul></body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 2


def test_parse_no_flights_found(parser):
    """HTML sans .pIav2d lève ParsingError."""
    html = "<html><body><div>No flights here</div></body></html>"
    with pytest.raises(ParsingError) as exc_info:
        parser.parse(html)
    assert "No flights found" in str(exc_info.value)


def test_parse_stops_nonstop(parser):
    """Vol direct (Non-stop) → stops=0."""
    html = """
    <html><body><ul>
    <li class="pIav2d">
        <div aria-label="À partir de 500 euros. Départ de Paris à 10:00, arrivée à Tokyo à 14:00. Durée totale : 4h 00min. Vol direct avec Air France."></div>
    </li>
    </ul></body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].stops == 0


def test_parse_stops_multiple(parser):
    """Vol avec escales → stops=2."""
    html = """
    <html><body><ul>
    <li class="pIav2d">
        <div aria-label="À partir de 500 euros. Départ de Paris à 10:00, arrivée à Tokyo à 22:00. Durée totale : 12h 00min. 2 escales avec Air France."></div>
    </li>
    </ul></body></html>
    """
    flights = parser.parse(html)
    assert len(flights) == 1
    assert flights[0].stops == 2
