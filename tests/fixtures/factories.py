"""Factories pour créer objets de tests avec paramètres configurables."""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from app.core.config import Settings
from app.models.google_flight_dto import GoogleFlightDTO
from app.models.request import DateRange, SearchRequest
from app.services.flight_parser import FlightParser
from tests.fixtures.helpers import TEMPLATE_URL, get_date_range, get_future_date


@pytest.fixture
def search_request_factory():
    """Factory pour créer SearchRequest (objet ou dict) avec dates dynamiques."""

    def _create(days_segment1=2, days_segment2=2, offset_segment2=10, as_dict=False):
        tomorrow = get_future_date(1)

        segments = [
            DateRange(
                start=tomorrow.isoformat(),
                end=(tomorrow + timedelta(days=days_segment1)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=offset_segment2)).isoformat(),
                end=(
                    tomorrow + timedelta(days=offset_segment2 + days_segment2)
                ).isoformat(),
            ),
        ]

        if as_dict:
            return {
                "template_url": TEMPLATE_URL,
                "segments_date_ranges": [
                    {"start": seg.start, "end": seg.end} for seg in segments
                ],
            }

        return SearchRequest(
            template_url=TEMPLATE_URL,
            segments_date_ranges=segments,
        )

    return _create


@pytest.fixture
def date_range_factory():
    """Factory pour créer DateRange (objet ou dict) avec offset configurables."""

    def _create(
        start_offset=1, duration=6, past=False, invalid_format=False, as_dict=False
    ):
        start_date, end_date = get_date_range(start_offset, duration, past)

        if as_dict:
            if invalid_format:
                return {
                    "start": start_date.strftime("%d-%m-%Y"),
                    "end": end_date.strftime("%d-%m-%Y"),
                }
            return {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }

        return DateRange(
            start=start_date.isoformat(),
            end=end_date.isoformat(),
        )

    return _create


@pytest.fixture
def flight_dto_factory():
    """Factory pour créer GoogleFlightDTO avec defaults."""

    def _create(
        price=1000.0,
        airline="Test Airline",
        departure_time="10:00",
        arrival_time="20:00",
        duration="10h 00min",
        stops=0,
        departure_airport="Paris",
        arrival_airport="Tokyo",
    ):
        return GoogleFlightDTO(
            price=price,
            airline=airline,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration=duration,
            stops=stops,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
        )

    return _create


@pytest.fixture
def settings_env_factory(monkeypatch):
    """Factory pour créer env Settings avec defaults."""

    def _create(**overrides):
        defaults = {
            "LOG_LEVEL": "INFO",
            "DECODO_USERNAME": "testuser",
            "DECODO_PASSWORD": "password123",
            "DECODO_PROXY_HOST": "fr.decodo.com:40000",
            "PROXY_ROTATION_ENABLED": "true",
            "CAPTCHA_DETECTION_ENABLED": "true",
            "DECODO_PROXY_ENABLED": "true",
        }
        env_vars = {**defaults, **overrides}
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return Settings()

    return _create


@pytest.fixture
def flight_parser_mock_factory():
    """Factory pour mocker FlightParser avec nombre configurable de vols."""

    def _create(num_flights=1, base_price=500.0, price_increment=100.0):
        parser = MagicMock(spec=FlightParser)
        parser.parse.return_value = [
            GoogleFlightDTO(
                price=float(base_price + i * price_increment),
                airline=f"Airline {i}" if num_flights > 1 else "Test Airline",
                departure_time="10:00",
                arrival_time="20:00",
                duration="10h 00min",
                stops=0,
            )
            for i in range(num_flights)
        ]
        return parser

    return _create


@pytest.fixture
def flight_parser_mock_single_factory(flight_parser_mock_factory):
    """Mock FlightParser retournant 1 vol valide (tests retry)."""
    return flight_parser_mock_factory(num_flights=1, base_price=500.0)


@pytest.fixture
def flight_parser_mock_10_flights_factory(flight_parser_mock_factory):
    """Mock FlightParser retournant 10 vols."""
    return flight_parser_mock_factory(num_flights=10, base_price=1000.0)


@pytest.fixture
def proxy_config_factory():
    """Factory pour créer ProxyConfig avec paramètres configurables."""
    from app.models.proxy import ProxyConfig

    def _create(
        host="fr.decodo.com",
        port=40000,
        username="testuser",
        password="testpass",
        country="FR",
    ):
        return ProxyConfig(
            host=host,
            port=port,
            username=username,
            password=password,
            country=country,
        )

    return _create
