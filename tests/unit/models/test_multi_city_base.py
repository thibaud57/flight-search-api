import pytest
from pydantic import ValidationError

from app.models import MultiCitySearchRequestBase
from tests.fixtures.helpers import GOOGLE_FLIGHT_TEMPLATE_URL


def test_multi_city_base_valid_two_segments(date_range_factory):
    """Test MultiCitySearchRequestBase avec 2 segments valides."""
    segment1 = date_range_factory(start_offset=1, duration=6)
    segment2 = date_range_factory(start_offset=7, duration=6)

    request = MultiCitySearchRequestBase(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[segment1, segment2],
    )

    assert len(request.segments_date_ranges) == 2


def test_multi_city_base_max_days_validation_ok(date_range_factory):
    """Test validation 15 jours max par segment (OK)."""
    segment1 = date_range_factory(start_offset=1, duration=15)
    segment2 = date_range_factory(start_offset=16, duration=15)

    request = MultiCitySearchRequestBase(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[segment1, segment2],
    )

    assert len(request.segments_date_ranges) == 2


def test_multi_city_base_max_days_validation_fails(date_range_factory):
    """Test validation 15 jours max par segment (FAIL)."""
    segment = date_range_factory(start_offset=1, duration=16)

    with pytest.raises(ValidationError) as exc_info:
        MultiCitySearchRequestBase(
            template_url="https://example.com/flights",
            segments_date_ranges=[segment],
        )

    assert "Segment 1 date range too large: 16 days" in str(exc_info.value)


def test_multi_city_base_chronological_order_ok(date_range_factory):
    """Test validation ordre chronologique segments (OK)."""
    segment1 = date_range_factory(start_offset=1, duration=7)
    segment2 = date_range_factory(start_offset=8, duration=7)

    request = MultiCitySearchRequestBase(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[segment1, segment2],
    )

    assert len(request.segments_date_ranges) == 2


def test_multi_city_base_chronological_order_fails(date_range_factory):
    """Test validation ordre chronologique segments (FAIL overlap)."""
    segment1 = date_range_factory(start_offset=1, duration=7)
    segment2 = date_range_factory(start_offset=5, duration=7)

    with pytest.raises(ValidationError) as exc_info:
        MultiCitySearchRequestBase(
            template_url="https://example.com/flights",
            segments_date_ranges=[segment1, segment2],
        )

    assert "Segment 2 overlaps with segment 1" in str(exc_info.value)


def test_multi_city_base_explosion_combinatoire_ok(date_range_factory):
    """Test validation max 1000 combinaisons (OK)."""
    segment1 = date_range_factory(start_offset=1, duration=10)
    segment2 = date_range_factory(start_offset=11, duration=10)

    request = MultiCitySearchRequestBase(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[segment1, segment2],
    )

    assert len(request.segments_date_ranges) == 2


def test_multi_city_base_explosion_combinatoire_fails(date_range_factory):
    """Test validation max 1000 combinaisons (FAIL - 16*16*16 = 4096)."""
    segment1 = date_range_factory(start_offset=1, duration=15)
    segment2 = date_range_factory(start_offset=16, duration=15)
    segment3 = date_range_factory(start_offset=31, duration=15)

    with pytest.raises(ValidationError) as exc_info:
        MultiCitySearchRequestBase(
            template_url="https://example.com/flights",
            segments_date_ranges=[segment1, segment2, segment3],
        )

    assert "Too many combinations:" in str(exc_info.value)
    assert "Max 1000 allowed" in str(exc_info.value)


def test_multi_city_base_extra_forbid(date_range_factory):
    """Test MultiCitySearchRequestBase rejette champs extra."""
    segment = date_range_factory(start_offset=1, duration=7)

    with pytest.raises(ValidationError) as exc_info:
        MultiCitySearchRequestBase(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=[segment],
            extra_field="invalid",
        )

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_multi_city_base_serialization(date_range_factory):
    """Test MultiCitySearchRequestBase sérialisation JSON."""
    segment = date_range_factory(start_offset=1, duration=7)

    request = MultiCitySearchRequestBase(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[segment],
    )

    json_data = request.model_dump()

    assert json_data["template_url"] == GOOGLE_FLIGHT_TEMPLATE_URL
    assert len(json_data["segments_date_ranges"]) == 1
    assert json_data["segments_date_ranges"][0]["start"] == segment.start
