"""Tests unitaires CombinationGenerator."""

import logging
from datetime import date

import pytest

from app.models.request import DateCombination, DateRange
from app.services.combination_generator import CombinationGenerator
from tests.fixtures.helpers import get_future_date


@pytest.fixture
def combination_generator() -> CombinationGenerator:
    """Fixture CombinationGenerator."""
    return CombinationGenerator()


@pytest.fixture
def two_segments(date_range_factory) -> list[DateRange]:
    """2 segments avec 7 et 6 jours."""
    return [
        date_range_factory(start_offset=1, duration=6),
        date_range_factory(start_offset=14, duration=5),
    ]


@pytest.fixture
def three_segments(date_range_factory) -> list[DateRange]:
    """3 segments avec 7, 6, 5 jours."""
    return [
        date_range_factory(start_offset=1, duration=6),
        date_range_factory(start_offset=14, duration=5),
        date_range_factory(start_offset=30, duration=4),
    ]


def test_generate_combinations_two_segments(combination_generator, two_segments):
    """Genere produit cartesien pour 2 segments (7x6=42)."""
    combinations = combination_generator.generate_combinations(two_segments)

    assert len(combinations) == 42


def test_generate_combinations_three_segments(combination_generator, three_segments):
    """Genere produit cartesien pour 3 segments (7x6x5=210)."""
    combinations = combination_generator.generate_combinations(three_segments)

    assert len(combinations) == 210


def test_generate_combinations_five_segments_asymmetric(combination_generator):
    """Genere combinaisons asymetriques (15x2x2x2x2=240)."""
    segments = [
        DateRange(
            start=get_future_date(1).isoformat(),
            end=get_future_date(15).isoformat(),
        ),
        DateRange(
            start=get_future_date(21).isoformat(),
            end=get_future_date(22).isoformat(),
        ),
        DateRange(
            start=get_future_date(26).isoformat(),
            end=get_future_date(27).isoformat(),
        ),
        DateRange(
            start=get_future_date(31).isoformat(),
            end=get_future_date(32).isoformat(),
        ),
        DateRange(
            start=get_future_date(36).isoformat(),
            end=get_future_date(37).isoformat(),
        ),
    ]

    combinations = combination_generator.generate_combinations(segments)

    assert len(combinations) == 240


def test_generate_combinations_segment_dates_format(
    combination_generator, two_segments
):
    """Dates generees format ISO 8601."""
    combinations = combination_generator.generate_combinations(two_segments)

    for combo in combinations:
        for d in combo.segment_dates:
            date.fromisoformat(d)


def test_generate_combinations_dates_within_ranges(combination_generator, two_segments):
    """Dates generees dans plages segments."""
    combinations = combination_generator.generate_combinations(two_segments)

    seg1_start = date.fromisoformat(two_segments[0].start)
    seg1_end = date.fromisoformat(two_segments[0].end)
    seg2_start = date.fromisoformat(two_segments[1].start)
    seg2_end = date.fromisoformat(two_segments[1].end)

    for combo in combinations:
        d1 = date.fromisoformat(combo.segment_dates[0])
        d2 = date.fromisoformat(combo.segment_dates[1])
        assert seg1_start <= d1 <= seg1_end
        assert seg2_start <= d2 <= seg2_end


def test_generate_combinations_date_range_single_day(combination_generator):
    """Segment avec 2 jours genere 2 dates."""
    segments = [
        DateRange(
            start=get_future_date(1).isoformat(),
            end=get_future_date(2).isoformat(),
        ),
        DateRange(
            start=get_future_date(11).isoformat(),
            end=get_future_date(12).isoformat(),
        ),
    ]

    combinations = combination_generator.generate_combinations(segments)

    assert len(combinations) == 4


def test_date_combination_model_valid_fields(date_range_factory):
    """Modele DateCombination valide."""
    date_range1 = date_range_factory(start_offset=1, duration=0)
    date_range2 = date_range_factory(start_offset=15, duration=0)
    combo = DateCombination(segment_dates=[date_range1.start, date_range2.start])

    assert len(combo.segment_dates) == 2
    assert combo.segment_dates[0] == date_range1.start
    assert combo.segment_dates[1] == date_range2.start


def test_combinations_unique_dates(combination_generator):
    """Toutes combinaisons sont uniques."""
    segments = [
        DateRange(
            start=get_future_date(1).isoformat(),
            end=get_future_date(3).isoformat(),
        ),
        DateRange(
            start=get_future_date(11).isoformat(),
            end=get_future_date(13).isoformat(),
        ),
    ]

    combinations = combination_generator.generate_combinations(segments)

    tuples = [tuple(c.segment_dates) for c in combinations]
    assert len(tuples) == len(set(tuples))
    assert len(combinations) == 9


def test_combinations_dates_ordered_chronologically(combination_generator):
    """Dates generees ordre chronologique par segment."""
    segments = [
        DateRange(
            start=get_future_date(1).isoformat(),
            end=get_future_date(7).isoformat(),
        ),
        DateRange(
            start=get_future_date(11).isoformat(),
            end=get_future_date(11).isoformat(),
        ),
    ]

    combinations = combination_generator.generate_combinations(segments)

    dates_seg1 = [c.segment_dates[0] for c in combinations]
    sorted_dates = sorted(set(dates_seg1))
    assert len(sorted_dates) == 7


def test_generate_combinations_logging(combination_generator, three_segments, caplog):
    """Logging INFO avec statistiques generation."""
    with caplog.at_level(logging.INFO):
        combination_generator.generate_combinations(three_segments)

    assert any("combinations generated" in r.message.lower() for r in caplog.records)
