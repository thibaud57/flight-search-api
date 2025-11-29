"""Factories pour créer objets de tests avec paramètres configurables."""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from app.core import Settings
from app.models import (
    DateRange,
    FlightCombinationResult,
    GoogleFlightDTO,
    GoogleSearchRequest,
    KayakFlightDTO,
    KayakSearchRequest,
    LayoverInfo,
    ProxyConfig,
    SearchStats,
)
from app.services import GoogleFlightParser
from tests.fixtures.helpers import (
    GOOGLE_FLIGHT_TEMPLATE_URL,
    KAYAK_TEMPLATE_URL,
    get_date_range,
    get_future_date,
)


def _create_segment_ranges(
    days_segment1: int = 2, days_segment2: int = 2, offset_segment2: int = 10
) -> list[DateRange]:
    """Helper interne pour générer segments DateRange standards (2 segments)."""
    tomorrow = get_future_date(1)
    return [
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


@pytest.fixture
def google_search_request_factory():
    """Factory pour créer GoogleSearchRequest (objet ou dict) avec dates dynamiques."""

    def _create(days_segment1=2, days_segment2=2, offset_segment2=10, as_dict=False):
        segments = _create_segment_ranges(days_segment1, days_segment2, offset_segment2)

        if as_dict:
            return {
                "template_url": GOOGLE_FLIGHT_TEMPLATE_URL,
                "segments_date_ranges": [
                    {"start": seg.start, "end": seg.end} for seg in segments
                ],
            }

        return GoogleSearchRequest(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=segments,
        )

    return _create


@pytest.fixture
def kayak_search_request_factory():
    """Factory pour créer KayakSearchRequest (objet ou dict) avec dates dynamiques."""

    def _create(days_segment1=2, days_segment2=2, offset_segment2=10, as_dict=False):
        segments = _create_segment_ranges(days_segment1, days_segment2, offset_segment2)

        if as_dict:
            return {
                "template_url": KAYAK_TEMPLATE_URL,
                "segments_date_ranges": [
                    {"start": seg.start, "end": seg.end} for seg in segments
                ],
            }

        return KayakSearchRequest(
            template_url=KAYAK_TEMPLATE_URL,
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
def google_flight_dto_factory():
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
def kayak_flight_dto_factory():
    """Factory pour créer KayakFlightDTO avec defaults."""

    def _create(
        price=1000.0,
        airline="Test Airline",
        departure_time="2026-01-14T10:00:00",
        arrival_time="2026-01-14T20:00:00",
        duration="10:00",
        departure_airport="CDG",
        arrival_airport="NRT",
        num_layovers=0,
        as_dict=False,
    ):
        layovers = []
        if num_layovers > 0:
            layovers = [
                LayoverInfo(airport=f"JF{i}", duration=f"{(i + 1):02d}:00")
                for i in range(num_layovers)
            ]

        if as_dict:
            return {
                "price": price,
                "airline": airline,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "duration": duration,
                "departure_airport": departure_airport,
                "arrival_airport": arrival_airport,
                "layovers": [
                    {"airport": lay.airport, "duration": lay.duration}
                    for lay in layovers
                ],
            }

        return KayakFlightDTO(
            price=price,
            airline=airline,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration=duration,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            layovers=layovers,
        )

    return _create


@pytest.fixture
def settings_env_factory(monkeypatch):
    """Factory pour créer env Settings avec defaults."""

    def _create(**overrides):
        defaults = {
            "LOG_LEVEL": "INFO",
            "PROXY_USERNAME": "testuser",
            "PROXY_PASSWORD": "password123",
            "PROXY_HOST": "proxy.example.com:40000",
            "PROXY_ROTATION_ENABLED": "true",
            "CAPTCHA_DETECTION_ENABLED": "true",
        }
        env_vars = {**defaults, **overrides}
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return Settings()

    return _create


@pytest.fixture
def google_flight_parser_mock_factory():
    """Factory pour mocker GoogleFlightParser avec nombre configurable de vols."""

    def _create(num_flights=1, base_price=500.0, price_increment=100.0):
        parser = MagicMock(spec=GoogleFlightParser)
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
def google_flight_parser_mock_10_flights_factory(google_flight_parser_mock_factory):
    """Mock GoogleFlightParser retournant 10 vols."""
    return google_flight_parser_mock_factory(num_flights=10, base_price=1000.0)


@pytest.fixture
def proxy_config_factory():
    """Factory pour créer ProxyConfig avec paramètres configurables."""

    def _create(
        host="proxy.example.com",
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


@pytest.fixture
def google_flights_html_factory():
    """Factory pour générer HTML Google Flights avec structure réelle."""

    def _create(
        num_flights=1,
        base_price=500.0,
        price_increment=100.0,
        airline_prefix="Airline",
        departure_airport="Paris",
        arrival_airport="Tokyo",
        include_wrapper=True,
    ):
        """Génère HTML Google Flights mock."""
        flights_html = ""
        for i in range(num_flights):
            price = int(base_price + i * price_increment)
            airline = f"{airline_prefix} {i}" if num_flights > 1 else airline_prefix
            departure_time = f"10:{i:02d}"
            arrival_time = f"14:{i:02d}"

            flights_html += f"""
        <li class="pIav2d">
            <div aria-label="À partir de {price} euros. Départ de {departure_airport} à {departure_time}, arrivée à {arrival_airport} à {arrival_time}. Durée totale : 4 h 00 min. Vol direct avec {airline}."></div>
        </li>
        """

        if include_wrapper:
            return f"<html><body><ul>{flights_html}</ul></body></html>"
        return flights_html

    return _create


@pytest.fixture
def kayak_poll_data_factory():
    """Factory pour générer poll_data Kayak avec structure réelle."""

    def _create(
        num_results: int = 3,
        base_price: float = 1000.0,
        price_increment: float = 100.0,
        with_multi_segment: bool = True,
        with_layover: bool = True,
        with_missing_fields: bool = True,
    ):
        """Génère poll_data JSON Kayak avec structure réelle dénormalisée."""
        results = []
        legs = {}
        segments = {}

        for i in range(num_results):
            result_id = f"result_{i}"
            leg_id = f"leg_{i}"
            price = base_price + i * price_increment

            # Result avec bookingOptions
            results.append(
                {
                    "resultId": result_id,
                    "type": "core",
                    "bookingOptions": [
                        {
                            "bookingId": f"booking_{i}",
                            "providerCode": "kayak",
                            "displayPrice": {
                                "price": price,
                                "currency": "EUR",
                                "localizedPrice": f"{int(price)} €",
                            },
                            "legFarings": [
                                {
                                    "legId": leg_id,
                                    "approxDepartureTime": "10:00",
                                    "approxArrivalTime": "20:00",
                                }
                            ],
                        }
                    ],
                }
            )

            # Leg avec segments
            if i == 0 and with_multi_segment:
                # Premier result : multi-segments avec layover
                segment_ids = [f"segment_{i}_1", f"segment_{i}_2"]
                leg_segments = [
                    {
                        "id": segment_ids[0],
                        "layover": {"duration": 120, "isLong": False}
                        if with_layover
                        else None,
                    },
                    {"id": segment_ids[1]},
                ]
                # Filtrer None si pas de layover
                leg_segments = [
                    {k: v for k, v in seg.items() if v is not None}
                    for seg in leg_segments
                ]

                legs[leg_id] = {
                    "duration": 1650,
                    "segments": leg_segments,
                    "arrival": "2026-05-07T06:00:00",
                    "departure": "2026-05-06T09:30:00",
                }

                # Segments correspondants
                segments[segment_ids[0]] = {
                    "airline": "AF",
                    "flightNumber": "123",
                    "origin": "CDG",
                    "destination": "JFK",
                    "departure": "2026-05-06T09:30:00",
                    "arrival": "2026-05-06T12:45:00",
                    "duration": 465,
                }
                segments[segment_ids[1]] = {
                    "airline": "VN",
                    "flightNumber": "311",
                    "origin": "JFK",
                    "destination": "NRT",
                    "departure": "2026-05-06T16:00:00",
                    "arrival": "2026-05-07T06:00:00",
                    "duration": 840,
                    "isOvernight": True,
                }

            elif i == num_results - 1 and with_missing_fields:
                # Dernier result : champs optionnels manquants
                segment_id = f"segment_{i}"
                legs[leg_id] = {
                    "duration": 480,
                    "segments": [{"id": segment_id}],
                    "arrival": "2026-02-01T22:00:00",
                    "departure": "2026-02-01T14:00:00",
                }
                segments[segment_id] = {
                    "airline": "BA",
                    "departure": "2026-02-01T14:00:00",
                    "arrival": "2026-02-01T22:00:00",
                    "duration": 480,
                }

            else:
                # Autres results : vol direct simple
                segment_id = f"segment_{i}"
                legs[leg_id] = {
                    "duration": 600,
                    "segments": [{"id": segment_id}],
                    "arrival": "2026-02-17T20:00:00",
                    "departure": "2026-02-17T10:00:00",
                }
                segments[segment_id] = {
                    "airline": "CZ",
                    "flightNumber": f"{5664 + i}",
                    "origin": "SHA",
                    "destination": "PKX",
                    "departure": "2026-02-17T10:00:00",
                    "arrival": "2026-02-17T20:00:00",
                    "duration": 600,
                }

        return {
            "searchId": "test_search_id",
            "searchUrl": {
                "url": "/flights/PAR-TYO/2026-02-06",
                "urlType": "relative",
            },
            "pageNumber": 1,
            "pageSize": 15,
            "sortMode": "price_a",
            "results": results,
            "legs": legs,
            "segments": segments,
        }

    return _create


@pytest.fixture
def search_stats_factory():
    """Factory pour créer SearchStats avec paramètres configurables."""

    def _create(total_results=10, search_time_ms=100, segments_count=2):
        return SearchStats(
            total_results=total_results,
            search_time_ms=search_time_ms,
            segments_count=segments_count,
        )

    return _create


@pytest.fixture
def flight_combination_result_factory(google_flight_dto_factory):
    """Factory pour créer FlightCombinationResult avec paramètres configurables."""

    def _create(
        num_flights=1,
        base_price=800.0,
        price_increment=100.0,
        segment_dates=None,
    ):
        if segment_dates is None:
            segment_dates = [
                get_future_date(1).isoformat(),
                get_future_date(15).isoformat(),
            ]

        flights = [
            google_flight_dto_factory(price=base_price + i * price_increment)
            for i in range(num_flights)
        ]

        total_price = sum(f.price or 0.0 for f in flights)

        return FlightCombinationResult(
            segment_dates=segment_dates,
            flights=flights,
            total_price=total_price if total_price > 0 else base_price,
        )

    return _create
