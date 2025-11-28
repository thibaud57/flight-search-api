from datetime import date

import pytest
from pydantic import ValidationError

from app.models import DateRange


def test_date_range_valid(date_range_factory):
    """Test création DateRange valide."""
    date_range = date_range_factory(start_offset=1, duration=6)

    assert date_range.start
    assert date_range.end


def test_date_range_start_after_end(date_range_factory):
    """Test DateRange échoue si start > end."""
    date_dict = date_range_factory(start_offset=1, duration=6, as_dict=True)

    with pytest.raises(ValidationError) as exc_info:
        DateRange(start=date_dict["end"], end=date_dict["start"])

    assert "End date must be greater than or equal to start date" in str(
        exc_info.value
    )


def test_date_range_same_day(date_range_factory):
    """Test DateRange accepte start == end (même jour)."""
    date_range = date_range_factory(start_offset=1, duration=0)

    assert date_range.start == date_range.end


def test_date_range_iso_format(date_range_factory):
    """Test DateRange valide format ISO 8601."""
    invalid_dict = date_range_factory(invalid_format=True, as_dict=True)

    with pytest.raises(ValidationError) as exc_info:
        DateRange(**invalid_dict)

    assert "Invalid ISO 8601 date format" in str(exc_info.value)


def test_date_range_extra_forbid(date_range_factory):
    """Test DateRange rejette champs extra."""
    date_dict = date_range_factory(as_dict=True)

    with pytest.raises(ValidationError) as exc_info:
        DateRange(**date_dict, extra_field="invalid")

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_date_range_serialization(date_range_factory):
    """Test DateRange sérialisation JSON."""
    date_range = date_range_factory(start_offset=1, duration=7)
    json_data = date_range.model_dump()

    assert "start" in json_data
    assert "end" in json_data
    assert json_data["start"] == date_range.start
    assert json_data["end"] == date_range.end


def test_date_range_days_diff(date_range_factory):
    """Test calcul différence jours entre start et end."""
    date_range = date_range_factory(start_offset=1, duration=6)

    start_date = date.fromisoformat(date_range.start)
    end_date = date.fromisoformat(date_range.end)
    days_diff = (end_date - start_date).days

    assert days_diff == 6


def test_date_range_future_only(date_range_factory):
    """Test DateRange rejette dates passées."""
    with pytest.raises(ValidationError) as exc_info:
        date_range_factory(start_offset=1, duration=6, past=True)

    assert "Start date must be today or in the future" in str(exc_info.value)
