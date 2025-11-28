"""Tests unitaires pour KayakSegment."""

import pytest
from pydantic import ValidationError

from app.models import KayakSegment


def test_segment_valid():
    """Segment valide avec codes IATA uppercase."""
    segment = KayakSegment(origin="PAR", destination="TYO", date="2026-01-14")

    assert segment.origin == "PAR"
    assert segment.destination == "TYO"
    assert segment.date == "2026-01-14"


@pytest.mark.parametrize(
    "origin,destination,date,field_error",
    [
        ("par", "TYO", "2026-01-14", "origin"),  # lowercase
        ("PARIS", "TYO", "2026-01-14", "origin"),  # longueur != 3
        ("Par", "Tyo", "2026-01-14", "origin"),  # mixedcase
        ("PAR", "", "2026-01-14", "destination"),  # destination vide
        ("PAR", "TYO", "14/01/2026", "date"),  # format non ISO
        ("PAR", "TYO", "2026-01", "date"),  # date incomplete
    ],
)
def test_segment_validation_errors(origin, destination, date, field_error):
    """Validation KayakSegment rejette valeurs invalides."""
    with pytest.raises(ValidationError) as exc_info:
        KayakSegment(origin=origin, destination=destination, date=date)

    assert field_error in str(exc_info.value).lower()


def test_segment_valid_future_date():
    """Dates futures lointaines doivent etre acceptees."""
    segment = KayakSegment(origin="PAR", destination="TYO", date="2030-12-31")

    assert segment.date == "2030-12-31"
