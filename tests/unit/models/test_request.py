"""Tests pour app/models/request.py (Provider, DateRange, MultiCitySearchRequestBase, GoogleSearchRequest, KayakSearchRequest)."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models import (
    DateRange,
    GoogleSearchRequest,
    KayakSearchRequest,
    MultiCitySearchRequestBase,
)
from tests.fixtures.helpers import (
    GOOGLE_FLIGHT_TEMPLATE_URL,
    KAYAK_TEMPLATE_URL,
    get_date_range,
    get_future_date,
)


# === DateRange Tests ===


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


# === MultiCitySearchRequestBase Tests ===


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


# === GoogleSearchRequest Tests ===


def test_google_search_request_valid_two_segments(google_search_request_factory):
    """Test GoogleSearchRequest valide avec 2 segments (minimum)."""
    request = google_search_request_factory(
        days_segment1=6, days_segment2=5, offset_segment2=7
    )

    assert len(request.segments_date_ranges) == 2


@pytest.mark.parametrize(
    "num_segments,should_fail",
    [
        (1, True),  # minimum 2 segments
        (2, False),  # valid
        (5, False),  # maximum 5 segments
        (6, True),  # too many segments
    ],
)
def test_google_search_request_segments_count_validation(num_segments, should_fail):
    """Test validation nombre segments GoogleSearchRequest (2-5)."""
    segments_date_ranges = []
    for i in range(num_segments):
        start = get_future_date(1 + i * 10)
        end = get_future_date(1 + i * 10 + 2)
        segments_date_ranges.append(
            DateRange(start=start.isoformat(), end=end.isoformat())
        )

    if should_fail:
        with pytest.raises(ValidationError):
            GoogleSearchRequest(
                template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
                segments_date_ranges=segments_date_ranges,
            )
    else:
        request = GoogleSearchRequest(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=segments_date_ranges,
        )
        assert len(request.segments_date_ranges) == num_segments


def test_google_search_request_empty_segments_fails():
    """Test GoogleSearchRequest rejette segments vide."""
    with pytest.raises(ValidationError):
        GoogleSearchRequest(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=[],
        )


def test_google_search_request_explosion_combinatoire_ok():
    """Test GoogleSearchRequest accepte 1000 combinaisons exactement."""
    request = GoogleSearchRequest(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=get_future_date(1).isoformat(),
                end=get_future_date(10).isoformat(),
            ),
            DateRange(
                start=get_future_date(11).isoformat(),
                end=get_future_date(12).isoformat(),
            ),
            DateRange(
                start=get_future_date(21).isoformat(),
                end=get_future_date(25).isoformat(),
            ),
            DateRange(
                start=get_future_date(31).isoformat(),
                end=get_future_date(32).isoformat(),
            ),
            DateRange(
                start=get_future_date(41).isoformat(),
                end=get_future_date(45).isoformat(),
            ),
        ],
    )

    assert len(request.segments_date_ranges) == 5


def test_google_search_request_explosion_combinatoire_fails():
    """Test GoogleSearchRequest rejette plus de 1000 combinaisons."""
    with pytest.raises(ValidationError) as exc_info:
        GoogleSearchRequest(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=[
                DateRange(
                    start=get_future_date(1).isoformat(),
                    end=get_future_date(15).isoformat(),
                ),
                DateRange(
                    start=get_future_date(21).isoformat(),
                    end=get_future_date(35).isoformat(),
                ),
                DateRange(
                    start=get_future_date(41).isoformat(),
                    end=get_future_date(55).isoformat(),
                ),
                DateRange(
                    start=get_future_date(61).isoformat(),
                    end=get_future_date(62).isoformat(),
                ),
                DateRange(
                    start=get_future_date(71).isoformat(),
                    end=get_future_date(72).isoformat(),
                ),
            ],
        )

    assert "Too many combinations" in str(exc_info.value)


def test_google_search_request_explosion_message_suggests_reduction():
    """Test GoogleSearchRequest message erreur suggère segment à réduire."""
    with pytest.raises(ValidationError) as exc_info:
        GoogleSearchRequest(
            template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
            segments_date_ranges=[
                DateRange(
                    start=get_future_date(1).isoformat(),
                    end=get_future_date(10).isoformat(),
                ),
                DateRange(
                    start=get_future_date(21).isoformat(),
                    end=get_future_date(35).isoformat(),
                ),
                DateRange(
                    start=get_future_date(51).isoformat(),
                    end=get_future_date(65).isoformat(),
                ),
            ],
        )
    error_msg = str(exc_info.value)

    assert "date range too large" in error_msg.lower() or "15 days" in error_msg


def test_google_search_request_asymmetric_ranges_valid():
    """Test GoogleSearchRequest accepte ranges asymétriques optimisés."""
    request = GoogleSearchRequest(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=get_future_date(1).isoformat(),
                end=get_future_date(15).isoformat(),
            ),
            DateRange(
                start=get_future_date(21).isoformat(),
                end=get_future_date(22).isoformat(),
            ),
            DateRange(
                start=get_future_date(31).isoformat(),
                end=get_future_date(32).isoformat(),
            ),
            DateRange(
                start=get_future_date(41).isoformat(),
                end=get_future_date(42).isoformat(),
            ),
            DateRange(
                start=get_future_date(51).isoformat(),
                end=get_future_date(52).isoformat(),
            ),
        ],
    )

    assert len(request.segments_date_ranges) == 5


def test_google_search_request_missing_fields_fails():
    """Test GoogleSearchRequest rejette champs requis manquants."""
    with pytest.raises(ValidationError):
        GoogleSearchRequest()


def test_google_search_request_model_dump_json_valid():
    """Test GoogleSearchRequest sérialisation JSON valide."""
    request = GoogleSearchRequest(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=get_future_date(1).isoformat(),
                end=get_future_date(6).isoformat(),
            ),
            DateRange(
                start=get_future_date(11).isoformat(),
                end=get_future_date(15).isoformat(),
            ),
        ],
    )
    json_str = request.model_dump_json()

    assert json_str is not None
    assert "template_url" in json_str
    assert "google.com/travel/flights" in json_str


def test_google_search_request_type_hints_pep695_compliant():
    """Test GoogleSearchRequest type hints conformes PEP 695."""
    segments_annotation = GoogleSearchRequest.model_fields[
        "segments_date_ranges"
    ].annotation

    assert "list" in str(segments_annotation)


def test_google_search_request_template_url_validation_valid():
    """Test GoogleSearchRequest validation URL Google Flights valide."""
    request = GoogleSearchRequest(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=get_future_date(1).isoformat(),
                end=get_future_date(3).isoformat(),
            ),
            DateRange(
                start=get_future_date(5).isoformat(),
                end=get_future_date(7).isoformat(),
            ),
        ],
    )

    assert "google.com/travel/flights" in request.template_url
    assert "tfs=" in request.template_url


def test_google_search_request_template_url_validation_invalid():
    """Test GoogleSearchRequest validation URL rejette URLs invalides."""
    with pytest.raises(ValidationError, match="URL must be a valid Google Flights URL"):
        GoogleSearchRequest(
            template_url="https://www.kayak.fr/flights",
            segments_date_ranges=[
                DateRange(
                    start=get_future_date(1).isoformat(),
                    end=get_future_date(3).isoformat(),
                ),
                DateRange(
                    start=get_future_date(5).isoformat(),
                    end=get_future_date(7).isoformat(),
                ),
            ],
        )


def test_google_search_request_template_url_missing_tfs():
    """Test GoogleSearchRequest validation URL rejette URL sans paramètre tfs."""
    with pytest.raises(ValidationError, match="URL template must contain 'tfs='"):
        GoogleSearchRequest(
            template_url="https://www.google.com/travel/flights",
            segments_date_ranges=[
                DateRange(
                    start=get_future_date(1).isoformat(),
                    end=get_future_date(3).isoformat(),
                ),
                DateRange(
                    start=get_future_date(5).isoformat(),
                    end=get_future_date(7).isoformat(),
                ),
            ],
        )


# === KayakSearchRequest Tests ===


def test_kayak_search_request_valid_two_segments(kayak_search_request_factory):
    """Test KayakSearchRequest valide avec 2 segments (minimum)."""
    request = kayak_search_request_factory(
        days_segment1=6, days_segment2=5, offset_segment2=7
    )

    assert len(request.segments_date_ranges) == 2


@pytest.mark.parametrize(
    "num_segments,should_fail",
    [
        (1, True),  # minimum 2 segments
        (2, False),  # valid
        (6, False),  # maximum 6 segments (Kayak)
        (7, True),  # too many segments
    ],
)
def test_kayak_search_request_segments_count_validation(num_segments, should_fail):
    """Test validation nombre segments KayakSearchRequest (2-6)."""
    segments_date_ranges = []
    for i in range(num_segments):
        start = get_future_date(1 + i * 10)
        end = get_future_date(1 + i * 10 + 2)
        segments_date_ranges.append(
            DateRange(start=start.isoformat(), end=end.isoformat())
        )

    if should_fail:
        with pytest.raises(ValidationError):
            KayakSearchRequest(
                template_url=KAYAK_TEMPLATE_URL,
                segments_date_ranges=segments_date_ranges,
            )
    else:
        request = KayakSearchRequest(
            template_url=KAYAK_TEMPLATE_URL,
            segments_date_ranges=segments_date_ranges,
        )
        assert len(request.segments_date_ranges) == num_segments


def test_kayak_search_request_empty_segments_fails():
    """Test KayakSearchRequest rejette segments vide."""
    with pytest.raises(ValidationError):
        KayakSearchRequest(
            template_url=KAYAK_TEMPLATE_URL,
            segments_date_ranges=[],
        )


@pytest.mark.parametrize(
    "invalid_url,error_msg",
    [
        ("https://www.google.com/travel/flights", "URL must be a valid Kayak URL"),
        ("https://www.kayak.fr/hotels", "URL must be a Kayak flights URL"),
        ("https://kayak.fr/flights", "URL must be a valid Kayak URL"),
    ],
)
def test_kayak_search_request_invalid_url(invalid_url, error_msg):
    """Test KayakSearchRequest validation URL rejette URLs invalides."""
    with pytest.raises(ValidationError, match=error_msg):
        KayakSearchRequest(
            template_url=invalid_url,
            segments_date_ranges=[
                DateRange(
                    start=get_future_date(1).isoformat(),
                    end=get_future_date(3).isoformat(),
                ),
                DateRange(
                    start=get_future_date(5).isoformat(),
                    end=get_future_date(7).isoformat(),
                ),
            ],
        )


def test_kayak_search_request_valid_url():
    """Test KayakSearchRequest URL Kayak valide acceptée."""
    request = KayakSearchRequest(
        template_url=KAYAK_TEMPLATE_URL,
        segments_date_ranges=[
            DateRange(
                start=get_future_date(1).isoformat(),
                end=get_future_date(3).isoformat(),
            ),
            DateRange(
                start=get_future_date(5).isoformat(),
                end=get_future_date(7).isoformat(),
            ),
        ],
    )

    assert request.template_url == KAYAK_TEMPLATE_URL
