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


def test_segment_invalid_origin_lowercase():
    """Codes IATA lowercase doivent etre rejetes."""
    with pytest.raises(ValidationError) as exc_info:
        KayakSegment(origin="par", destination="TYO", date="2026-01-14")

    assert "origin" in str(exc_info.value).lower()


def test_segment_invalid_origin_length():
    """Codes IATA longueur != 3 doivent etre rejetes."""
    with pytest.raises(ValidationError) as exc_info:
        KayakSegment(origin="PARIS", destination="TYO", date="2026-01-14")

    assert "origin" in str(exc_info.value).lower()


def test_segment_invalid_destination_empty():
    """Destination vide doit etre rejetee."""
    with pytest.raises(ValidationError) as exc_info:
        KayakSegment(origin="PAR", destination="", date="2026-01-14")

    assert "destination" in str(exc_info.value).lower()


def test_segment_invalid_date_format():
    """Dates non ISO-8601 doivent etre rejetees."""
    with pytest.raises(ValidationError) as exc_info:
        KayakSegment(origin="PAR", destination="TYO", date="14/01/2026")

    assert "date" in str(exc_info.value).lower()


def test_segment_invalid_date_partial():
    """Dates incompletes doivent etre rejetees."""
    with pytest.raises(ValidationError) as exc_info:
        KayakSegment(origin="PAR", destination="TYO", date="2026-01")

    assert "date" in str(exc_info.value).lower()


def test_segment_invalid_mixedcase_rejected():
    """Codes IATA mixedcase doivent etre rejetes (strategie stricte)."""
    with pytest.raises(ValidationError) as exc_info:
        KayakSegment(origin="Par", destination="Tyo", date="2026-01-14")

    assert "origin" in str(exc_info.value).lower()


def test_segment_valid_future_date():
    """Dates futures lointaines doivent etre acceptees."""
    segment = KayakSegment(origin="PAR", destination="TYO", date="2030-12-31")

    assert segment.date == "2030-12-31"
