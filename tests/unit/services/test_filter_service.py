"""Tests unitaires FilterService."""

import logging

import pytest

from app.models import LayoverInfo, SegmentFilters
from app.services import FilterService


@pytest.fixture
def filter_service() -> FilterService:
    """Fixture retournant instance FilterService."""
    return FilterService()


def test_apply_filters_none_returns_unchanged_list(
    filter_service: FilterService, kayak_flight_dto_factory
) -> None:
    """Filters None retourne liste inchangee."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="10:00"),
        kayak_flight_dto_factory(price=600.0, duration="12:00"),
        kayak_flight_dto_factory(price=700.0, duration="15:00"),
    ]

    result = filter_service.apply_filters(flights, filters=None, segment_index=0)

    assert result == flights
    assert len(result) == 3


def test_apply_filters_max_duration_excludes_long_flights(
    filter_service: FilterService, kayak_flight_dto_factory
) -> None:
    """Max duration exclut vols longs."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="08:00"),
        kayak_flight_dto_factory(price=600.0, duration="10:00"),
        kayak_flight_dto_factory(price=700.0, duration="12:00"),
    ]

    filters = SegmentFilters(max_duration="10:00")
    result = filter_service.apply_filters(flights, filters, segment_index=0)

    assert len(result) == 2
    assert result[0].duration == "08:00"
    assert result[1].duration == "10:00"


def test_apply_filters_max_stops_excludes_flights_with_stops(
    filter_service: FilterService, kayak_flight_dto_factory
) -> None:
    """Max stops exclut vols avec escales."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="08:00", num_layovers=0),
        kayak_flight_dto_factory(price=600.0, duration="10:00", num_layovers=1),
        kayak_flight_dto_factory(price=700.0, duration="12:00", num_layovers=2),
    ]

    filters = SegmentFilters(max_stops=1)
    result = filter_service.apply_filters(flights, filters, segment_index=0)

    assert len(result) == 2
    assert result[0].stops == 0
    assert result[1].stops == 1


def test_apply_filters_min_layover_duration_excludes_short_layovers(
    filter_service: FilterService, kayak_flight_dto_factory
) -> None:
    """Min layover duration exclut layovers courts."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="08:00", num_layovers=0),
        kayak_flight_dto_factory(
            price=600.0,
            duration="10:00",
            departure_airport="CDG",
            arrival_airport="NRT",
        ),
    ]
    flights[1].layovers = [LayoverInfo(airport="JFK", duration="00:30")]

    flight_long_layover = kayak_flight_dto_factory(
        price=700.0,
        duration="12:00",
        departure_airport="CDG",
        arrival_airport="NRT",
    )
    flight_long_layover.layovers = [LayoverInfo(airport="JFK", duration="02:00")]
    flights.append(flight_long_layover)

    filters = SegmentFilters(min_layover_duration="01:00")
    result = filter_service.apply_filters(flights, filters, segment_index=0)

    assert len(result) == 2
    assert result[0].stops == 0
    assert result[1].layovers[0].duration == "02:00"


def test_apply_filters_max_layover_duration_excludes_long_layovers(
    filter_service: FilterService, kayak_flight_dto_factory
) -> None:
    """Max layover duration exclut layovers longs."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="08:00", num_layovers=0),
        kayak_flight_dto_factory(
            price=600.0,
            duration="10:00",
            departure_airport="CDG",
            arrival_airport="NRT",
        ),
    ]
    flights[1].layovers = [LayoverInfo(airport="JFK", duration="01:00")]

    flight_long_layover = kayak_flight_dto_factory(
        price=700.0,
        duration="12:00",
        departure_airport="CDG",
        arrival_airport="NRT",
    )
    flight_long_layover.layovers = [LayoverInfo(airport="JFK", duration="05:00")]
    flights.append(flight_long_layover)

    filters = SegmentFilters(max_layover_duration="03:00")
    result = filter_service.apply_filters(flights, filters, segment_index=0)

    assert len(result) == 2
    assert result[0].stops == 0
    assert result[1].layovers[0].duration == "01:00"


def test_apply_filters_combined_filters_and_logic(
    filter_service: FilterService, kayak_flight_dto_factory
) -> None:
    """Filtres combines appliquent AND logic."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="08:00", num_layovers=0),
        kayak_flight_dto_factory(price=600.0, duration="10:00", num_layovers=1),
        kayak_flight_dto_factory(price=700.0, duration="15:00", num_layovers=2),
    ]

    filters = SegmentFilters(max_duration="12:00", max_stops=1)
    result = filter_service.apply_filters(flights, filters, segment_index=0)

    assert len(result) == 2
    assert result[0].duration == "08:00"
    assert result[0].stops == 0
    assert result[1].duration == "10:00"
    assert result[1].stops == 1


def test_apply_filters_no_flights_pass_returns_empty_list(
    filter_service: FilterService, kayak_flight_dto_factory
) -> None:
    """Aucun vol ne passe retourne liste vide."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="15:00"),
        kayak_flight_dto_factory(price=600.0, duration="16:00"),
        kayak_flight_dto_factory(price=700.0, duration="18:00"),
    ]

    filters = SegmentFilters(max_duration="10:00")
    result = filter_service.apply_filters(flights, filters, segment_index=0)

    assert result == []
    assert len(result) == 0


def test_apply_filters_invalid_duration_format_skips_flight_and_logs_warning(
    filter_service: FilterService, kayak_flight_dto_factory, caplog
) -> None:
    """Duration format invalide skip vol et log WARNING."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="08:00"),
        kayak_flight_dto_factory(price=600.0, duration="invalid"),
        kayak_flight_dto_factory(price=700.0, duration="10:00"),
    ]

    filters = SegmentFilters(max_duration="12:00")

    with caplog.at_level(logging.WARNING):
        result = filter_service.apply_filters(flights, filters, segment_index=0)

    assert len(result) == 2
    assert result[0].duration == "08:00"
    assert result[1].duration == "10:00"

    assert "Invalid duration format, skipping flight" in caplog.text


def test_apply_filters_direct_flight_ignores_layover_filters(
    filter_service: FilterService, kayak_flight_dto_factory
) -> None:
    """Vol direct layovers vide ignore filtres layover."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="08:00", num_layovers=0),
        kayak_flight_dto_factory(price=600.0, duration="09:00", num_layovers=0),
    ]

    filters = SegmentFilters(min_layover_duration="01:00", max_layover_duration="03:00")
    result = filter_service.apply_filters(flights, filters, segment_index=0)

    assert len(result) == 2
    assert all(len(f.layovers) == 0 for f in result)


def test_apply_filters_multiple_layovers_all_must_pass(
    filter_service: FilterService, kayak_flight_dto_factory
) -> None:
    """Multiple layovers - TOUTES doivent passer."""
    flight_valid = kayak_flight_dto_factory(
        price=500.0,
        duration="15:00",
        departure_airport="CDG",
        arrival_airport="NRT",
    )
    flight_valid.layovers = [
        LayoverInfo(airport="JFK", duration="01:30"),
        LayoverInfo(airport="LAX", duration="02:00"),
    ]

    flight_invalid = kayak_flight_dto_factory(
        price=600.0,
        duration="16:00",
        departure_airport="CDG",
        arrival_airport="NRT",
    )
    flight_invalid.layovers = [
        LayoverInfo(airport="JFK", duration="01:30"),
        LayoverInfo(airport="LAX", duration="00:30"),
    ]

    flights = [flight_valid, flight_invalid]

    filters = SegmentFilters(min_layover_duration="01:00", max_layover_duration="03:00")
    result = filter_service.apply_filters(flights, filters, segment_index=0)

    assert len(result) == 1
    assert result[0].price == 500.0
    assert len(result[0].layovers) == 2


def test_apply_filters_logging_structured_with_context(
    filter_service: FilterService, kayak_flight_dto_factory, caplog
) -> None:
    """Logging structure avec extra context."""
    flights = [
        kayak_flight_dto_factory(price=500.0, duration="08:00"),
        kayak_flight_dto_factory(price=600.0, duration="10:00"),
        kayak_flight_dto_factory(price=700.0, duration="15:00"),
    ]

    filters = SegmentFilters(max_duration="12:00")

    with caplog.at_level(logging.INFO):
        filter_service.apply_filters(flights, filters, segment_index=1)

    log_records = [
        record for record in caplog.records if record.message == "Filters applied"
    ]
    assert len(log_records) == 1

    log_record = log_records[0]
    assert hasattr(log_record, "segment_index")
    assert log_record.segment_index == 1
    assert hasattr(log_record, "filters_applied")
    assert log_record.filters_applied == {"max_duration": "12:00"}
    assert hasattr(log_record, "flights_before")
    assert log_record.flights_before == 3
    assert hasattr(log_record, "flights_after")
    assert log_record.flights_after == 2
