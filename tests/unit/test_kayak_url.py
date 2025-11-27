"""Tests unitaires pour generate_kayak_url."""

import pytest

from app.utils import KayakUrlError, generate_kayak_url


def test_generate_kayak_url_single_segment():
    """URL aller simple avec remplacement date."""
    template = "https://www.kayak.fr/flights/PAR-SLZ/2025-01-14?sort=bestflight_a"
    new_dates = ["2026-01-14"]

    url = generate_kayak_url(template, new_dates)

    assert url == "https://www.kayak.fr/flights/PAR-SLZ/2026-01-14?sort=bestflight_a"


def test_generate_kayak_url_two_segments():
    """URL aller-retour avec remplacement 2 dates."""
    template = "https://www.kayak.fr/flights/PAR-TYO/2025-03-15/TYO-PAR/2025-03-25?sort=bestflight_a"
    new_dates = ["2026-03-15", "2026-03-25"]

    url = generate_kayak_url(template, new_dates)

    assert (
        url
        == "https://www.kayak.fr/flights/PAR-TYO/2026-03-15/TYO-PAR/2026-03-25?sort=bestflight_a"
    )


def test_generate_kayak_url_three_segments_multicity():
    """URL multi-city 3 segments."""
    template = "https://www.kayak.fr/flights/PAR-SLZ/2025-01-14/SLZ-LIM/2025-03-28/LIM-PAR/2025-04-10?sort=bestflight_a"
    new_dates = ["2026-01-14", "2026-03-28", "2026-04-10"]

    url = generate_kayak_url(template, new_dates)

    assert (
        url
        == "https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a"
    )


def test_generate_kayak_url_invalid_date_format():
    """Date invalide leve KayakUrlError."""
    template = "https://www.kayak.fr/flights/PAR-TYO/2025-01-14?sort=bestflight_a"
    new_dates = ["2026/01/14"]  # Format invalide (slashes au lieu de tirets)

    with pytest.raises(KayakUrlError) as exc_info:
        generate_kayak_url(template, new_dates)

    assert "Date invalide" in str(exc_info.value)
    assert "2026/01/14" in str(exc_info.value)


def test_generate_kayak_url_mismatched_date_count():
    """Nombre dates different entre template et new_dates leve erreur."""
    template = "https://www.kayak.fr/flights/PAR-TYO/2025-01-14/TYO-PAR/2025-01-20?sort=bestflight_a"
    new_dates = ["2026-01-14"]  # Template a 2 dates, mais 1 seule fournie

    with pytest.raises(KayakUrlError) as exc_info:
        generate_kayak_url(template, new_dates)

    assert "Nombre de dates incorrect" in str(exc_info.value)
    assert "2 dates" in str(exc_info.value)
    assert "1 nouvelles dates" in str(exc_info.value)


def test_generate_kayak_url_preserves_other_params():
    """Preserve query params et path structure."""
    template = (
        "https://www.kayak.fr/flights/PAR-TYO/2025-06-01?sort=bestflight_a&fs=stops=0"
    )
    new_dates = ["2026-07-15"]

    url = generate_kayak_url(template, new_dates)

    assert "2026-07-15" in url
    assert "sort=bestflight_a" in url
    assert "fs=stops=0" in url
    assert "/PAR-TYO/" in url


def test_generate_kayak_url_six_segments():
    """URL multi-city 6 segments (max Kayak)."""
    template = (
        "https://www.kayak.fr/flights/"
        "PAR-NYC/2025-01-01/"
        "NYC-LON/2025-01-05/"
        "LON-TOK/2025-01-10/"
        "TOK-SYD/2025-01-15/"
        "SYD-DXB/2025-01-20/"
        "DXB-PAR/2025-01-25"
        "?sort=bestflight_a"
    )
    new_dates = [
        "2026-02-01",
        "2026-02-05",
        "2026-02-10",
        "2026-02-15",
        "2026-02-20",
        "2026-02-25",
    ]

    url = generate_kayak_url(template, new_dates)

    for date in new_dates:
        assert date in url
