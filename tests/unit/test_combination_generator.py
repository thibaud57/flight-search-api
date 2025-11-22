"""Tests unitaires CombinationGenerator."""

from datetime import date, timedelta

import pytest

from app.models.request import DateCombination, FlightSegment
from app.services.combination_generator import CombinationGenerator


@pytest.fixture
def combination_generator() -> CombinationGenerator:
    """Fixture CombinationGenerator."""
    return CombinationGenerator()


@pytest.fixture
def two_segments() -> list[FlightSegment]:
    """2 segments avec 7 et 6 jours."""
    tomorrow = date.today() + timedelta(days=1)
    return [
        FlightSegment(
            from_city="Paris",
            to_city="Tokyo",
            date_range={
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=6)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="Tokyo",
            to_city="New York",
            date_range={
                "start": (tomorrow + timedelta(days=14)).isoformat(),
                "end": (tomorrow + timedelta(days=19)).isoformat(),
            },
        ),
    ]


@pytest.fixture
def three_segments() -> list[FlightSegment]:
    """3 segments avec 7, 6, 5 jours."""
    tomorrow = date.today() + timedelta(days=1)
    return [
        FlightSegment(
            from_city="Paris",
            to_city="Tokyo",
            date_range={
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=6)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="Tokyo",
            to_city="Singapore",
            date_range={
                "start": (tomorrow + timedelta(days=14)).isoformat(),
                "end": (tomorrow + timedelta(days=19)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="Singapore",
            to_city="New York",
            date_range={
                "start": (tomorrow + timedelta(days=30)).isoformat(),
                "end": (tomorrow + timedelta(days=34)).isoformat(),
            },
        ),
    ]


def test_generate_combinations_two_segments(combination_generator, two_segments):
    """Test 1: Genere produit cartesien pour 2 segments (7x6=42)."""
    combinations = combination_generator.generate_combinations(two_segments)

    assert len(combinations) == 42


def test_generate_combinations_three_segments(combination_generator, three_segments):
    """Test 2: Genere produit cartesien pour 3 segments (7x6x5=210)."""
    combinations = combination_generator.generate_combinations(three_segments)

    assert len(combinations) == 210


def test_generate_combinations_five_segments_asymmetric(combination_generator):
    """Test 3: Genere combinaisons asymetriques (15x2x2x2x2=240)."""
    tomorrow = date.today() + timedelta(days=1)
    segments = [
        FlightSegment(
            from_city="AA",
            to_city="BB",
            date_range={
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=14)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="BB",
            to_city="CC",
            date_range={
                "start": (tomorrow + timedelta(days=20)).isoformat(),
                "end": (tomorrow + timedelta(days=21)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="CC",
            to_city="DD",
            date_range={
                "start": (tomorrow + timedelta(days=25)).isoformat(),
                "end": (tomorrow + timedelta(days=26)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="DD",
            to_city="EE",
            date_range={
                "start": (tomorrow + timedelta(days=30)).isoformat(),
                "end": (tomorrow + timedelta(days=31)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="EE",
            to_city="FF",
            date_range={
                "start": (tomorrow + timedelta(days=35)).isoformat(),
                "end": (tomorrow + timedelta(days=36)).isoformat(),
            },
        ),
    ]

    combinations = combination_generator.generate_combinations(segments)

    assert len(combinations) == 240


def test_generate_combinations_segment_dates_format(
    combination_generator, two_segments
):
    """Test 4: Dates generees format ISO 8601."""
    combinations = combination_generator.generate_combinations(two_segments)

    for combo in combinations:
        for d in combo.segment_dates:
            date.fromisoformat(d)


def test_generate_combinations_dates_within_ranges(combination_generator, two_segments):
    """Test 5: Dates generees dans plages segments."""
    combinations = combination_generator.generate_combinations(two_segments)

    seg1_start = date.fromisoformat(two_segments[0].date_range.start)
    seg1_end = date.fromisoformat(two_segments[0].date_range.end)
    seg2_start = date.fromisoformat(two_segments[1].date_range.start)
    seg2_end = date.fromisoformat(two_segments[1].date_range.end)

    for combo in combinations:
        d1 = date.fromisoformat(combo.segment_dates[0])
        d2 = date.fromisoformat(combo.segment_dates[1])
        assert seg1_start <= d1 <= seg1_end
        assert seg2_start <= d2 <= seg2_end


def test_generate_combinations_date_range_single_day(combination_generator):
    """Test 6: Segment avec 2 jours genere 2 dates."""
    tomorrow = date.today() + timedelta(days=1)
    segments = [
        FlightSegment(
            from_city="AA",
            to_city="BB",
            date_range={
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=1)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="BB",
            to_city="CC",
            date_range={
                "start": (tomorrow + timedelta(days=10)).isoformat(),
                "end": (tomorrow + timedelta(days=11)).isoformat(),
            },
        ),
    ]

    combinations = combination_generator.generate_combinations(segments)

    assert len(combinations) == 4


def test_date_combination_model_valid_fields():
    """Test 7: Modele DateCombination valide."""
    combo = DateCombination(segment_dates=["2025-06-01", "2025-06-15"])

    assert combo.segment_dates == ["2025-06-01", "2025-06-15"]


def test_combinations_unique_dates(combination_generator):
    """Test 8: Toutes combinaisons sont uniques."""
    tomorrow = date.today() + timedelta(days=1)
    segments = [
        FlightSegment(
            from_city="AA",
            to_city="BB",
            date_range={
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=2)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="BB",
            to_city="CC",
            date_range={
                "start": (tomorrow + timedelta(days=10)).isoformat(),
                "end": (tomorrow + timedelta(days=12)).isoformat(),
            },
        ),
    ]

    combinations = combination_generator.generate_combinations(segments)

    tuples = [tuple(c.segment_dates) for c in combinations]
    assert len(tuples) == len(set(tuples))
    assert len(combinations) == 9


def test_combinations_dates_ordered_chronologically(combination_generator):
    """Test 9: Dates generees ordre chronologique par segment."""
    tomorrow = date.today() + timedelta(days=1)
    segments = [
        FlightSegment(
            from_city="AA",
            to_city="BB",
            date_range={
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=6)).isoformat(),
            },
        ),
        FlightSegment(
            from_city="BB",
            to_city="CC",
            date_range={
                "start": (tomorrow + timedelta(days=10)).isoformat(),
                "end": (tomorrow + timedelta(days=10)).isoformat(),
            },
        ),
    ]

    combinations = combination_generator.generate_combinations(segments)

    dates_seg1 = [c.segment_dates[0] for c in combinations]
    sorted_dates = sorted(set(dates_seg1))
    assert len(sorted_dates) == 7


def test_generate_combinations_logging(combination_generator, three_segments, caplog):
    """Test 10: Logging INFO avec statistiques generation."""
    import logging

    with caplog.at_level(logging.INFO):
        combination_generator.generate_combinations(three_segments)

    assert any("combinations generated" in r.message.lower() for r in caplog.records)
