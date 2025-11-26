"""Tests unitaires pour KayakUrlBuilder."""

import pytest

from app.models import KayakSegment
from app.utils import KayakUrlBuilder


def test_build_url_single_segment():
    """URL aller simple."""
    builder = KayakUrlBuilder()
    segments = [KayakSegment(origin="PAR", destination="SLZ", date="2026-01-14")]

    url = builder.build_url(segments)

    assert url == "https://www.kayak.fr/flights/PAR-SLZ/2026-01-14?sort=bestflight_a"


def test_build_url_two_segments():
    """URL aller-retour."""
    builder = KayakUrlBuilder()
    segments = [
        KayakSegment(origin="PAR", destination="TYO", date="2026-03-15"),
        KayakSegment(origin="TYO", destination="PAR", date="2026-03-25"),
    ]

    url = builder.build_url(segments)

    assert (
        url
        == "https://www.kayak.fr/flights/PAR-TYO/2026-03-15/TYO-PAR/2026-03-25?sort=bestflight_a"
    )


def test_build_url_three_segments_multicity():
    """URL multi-city 3 segments."""
    builder = KayakUrlBuilder()
    segments = [
        KayakSegment(origin="PAR", destination="SLZ", date="2026-01-14"),
        KayakSegment(origin="SLZ", destination="LIM", date="2026-03-28"),
        KayakSegment(origin="LIM", destination="PAR", date="2026-04-10"),
    ]

    url = builder.build_url(segments)

    assert (
        url
        == "https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a"
    )


def test_build_url_six_segments_max():
    """URL 6 segments (limite max Kayak)."""
    builder = KayakUrlBuilder()
    segments = [
        KayakSegment(origin="PAR", destination="NYC", date="2026-01-10"),
        KayakSegment(origin="NYC", destination="TYO", date="2026-01-20"),
        KayakSegment(origin="TYO", destination="SYD", date="2026-02-01"),
        KayakSegment(origin="SYD", destination="SIN", date="2026-02-15"),
        KayakSegment(origin="SIN", destination="DXB", date="2026-03-01"),
        KayakSegment(origin="DXB", destination="PAR", date="2026-03-15"),
    ]

    url = builder.build_url(segments)

    assert "/PAR-NYC/2026-01-10" in url
    assert "/NYC-TYO/2026-01-20" in url
    assert "/TYO-SYD/2026-02-01" in url
    assert "/SYD-SIN/2026-02-15" in url
    assert "/SIN-DXB/2026-03-01" in url
    assert "/DXB-PAR/2026-03-15" in url
    assert url.endswith("?sort=bestflight_a")


def test_build_url_empty_segments():
    """Liste segments vide doit lever ValueError."""
    builder = KayakUrlBuilder()

    with pytest.raises(ValueError) as exc_info:
        builder.build_url([])

    assert (
        "empty" in str(exc_info.value).lower()
        or "at least" in str(exc_info.value).lower()
    )


def test_build_url_seven_segments_exceeds_limit():
    """Liste >6 segments doit lever ValueError."""
    builder = KayakUrlBuilder()
    segments = [
        KayakSegment(origin="PAR", destination="NYC", date="2026-01-10"),
        KayakSegment(origin="NYC", destination="TYO", date="2026-01-20"),
        KayakSegment(origin="TYO", destination="SYD", date="2026-02-01"),
        KayakSegment(origin="SYD", destination="SIN", date="2026-02-15"),
        KayakSegment(origin="SIN", destination="DXB", date="2026-03-01"),
        KayakSegment(origin="DXB", destination="LON", date="2026-03-15"),
        KayakSegment(origin="LON", destination="PAR", date="2026-03-25"),
    ]

    with pytest.raises(ValueError) as exc_info:
        builder.build_url(segments)

    assert "6" in str(exc_info.value) or "maximum" in str(exc_info.value).lower()


def test_build_url_custom_base_url():
    """Base URL personnalisee."""
    builder = KayakUrlBuilder(base_url="https://www.kayak.com")
    segments = [KayakSegment(origin="PAR", destination="SLZ", date="2026-01-14")]

    url = builder.build_url(segments)

    assert url.startswith("https://www.kayak.com/flights/")


def test_build_url_sort_param_present():
    """Query param sort toujours present."""
    builder = KayakUrlBuilder()
    segments = [KayakSegment(origin="PAR", destination="SLZ", date="2026-01-14")]

    url = builder.build_url(segments)

    assert url.endswith("?sort=bestflight_a")


def test_build_url_segment_separator():
    """Separateurs corrects entre codes et segments."""
    builder = KayakUrlBuilder()
    segments = [
        KayakSegment(origin="PAR", destination="TYO", date="2026-03-15"),
        KayakSegment(origin="TYO", destination="PAR", date="2026-03-25"),
    ]

    url = builder.build_url(segments)

    assert "PAR-TYO" in url
    assert "TYO-PAR" in url
    assert "/2026-03-15/" in url
    assert "/2026-03-25" in url


def test_build_url_no_trailing_slash():
    """Pas de slash final avant query param."""
    builder = KayakUrlBuilder()
    segments = [KayakSegment(origin="PAR", destination="SLZ", date="2026-01-14")]

    url = builder.build_url(segments)

    assert not url.replace("?sort=bestflight_a", "").endswith("/")
