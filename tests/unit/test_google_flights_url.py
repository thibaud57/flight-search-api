"""Tests unitaires pour generate_google_flights_url."""

import pytest

from app.utils import GoogleFlightsUrlError, generate_google_flights_url
from tests.fixtures.helpers import GOOGLE_FLIGHT_BASE_URL, GOOGLE_FLIGHT_TEMPLATE_URL


def test_generate_google_flights_url_valid_dates():
    """Génère URL avec dates valides."""
    new_dates = ["2026-06-01", "2026-06-07"]

    url = generate_google_flights_url(GOOGLE_FLIGHT_TEMPLATE_URL, new_dates)

    assert "tfs=" in url
    assert url.startswith("https://www.google.com/travel/flights")


def test_generate_google_flights_url_preserves_structure():
    """URL générée preserve scheme, netloc, path."""
    new_dates = ["2026-06-01", "2026-06-07"]

    url = generate_google_flights_url(GOOGLE_FLIGHT_TEMPLATE_URL, new_dates)

    assert url.startswith("https://www.google.com/travel/flights/search?tfs=")
    assert "tfs=" in url


def test_generate_google_flights_url_invalid_date_format():
    """Date invalide lève GoogleFlightsUrlError."""
    new_dates = ["2026/06/01", "2026-06-15"]

    with pytest.raises(GoogleFlightsUrlError) as exc_info:
        generate_google_flights_url(GOOGLE_FLIGHT_TEMPLATE_URL, new_dates)

    assert "Date invalide" in str(exc_info.value)
    assert "2026/06/01" in str(exc_info.value)


def test_generate_google_flights_url_missing_tfs_param():
    """URL sans paramètre tfs lève erreur."""
    new_dates = ["2026-06-01", "2026-06-15"]

    with pytest.raises(GoogleFlightsUrlError) as exc_info:
        generate_google_flights_url(GOOGLE_FLIGHT_BASE_URL, new_dates)

    assert "tfs" in str(exc_info.value).lower()


def test_generate_google_flights_url_invalid_base64():
    """Paramètre tfs invalide (non base64) lève erreur."""
    url_invalid_tfs = "https://www.google.com/travel/flights?tfs=invalid!!!base64"
    new_dates = ["2026-06-01", "2026-06-15"]

    with pytest.raises(GoogleFlightsUrlError) as exc_info:
        generate_google_flights_url(url_invalid_tfs, new_dates)

    assert "base64" in str(exc_info.value).lower()


def test_generate_google_flights_url_mismatched_date_count():
    """Nombre dates différent entre template et new_dates lève erreur."""
    new_dates = ["2026-06-01"]

    with pytest.raises(GoogleFlightsUrlError) as exc_info:
        generate_google_flights_url(GOOGLE_FLIGHT_TEMPLATE_URL, new_dates)

    assert "Nombre de dates incorrect" in str(exc_info.value)


def test_generate_google_flights_url_three_segments():
    """URL 3 segments multi-city."""
    template_3seg = "https://www.google.com/travel/flights/search?tfs=CBwQAhooEgoyMDI2LTAyLTAzagwIAxIIL20vMDVxdGpyDAgDEggvbS8wN2RmaxooEgoyMDI2LTAyLTA3agwIAxIIL20vMDlkNF9yDAgDEggvbS8wMTkxNBooEgoyMDI2LTAyLTExagwIAxIIL20vMDE5MTRyDAgDEggvbS8wNmM2MkABSAFwAYIBCwj___________8BmAED&hl=fr&gl=FR"
    new_dates = ["2026-07-01", "2026-07-07", "2026-07-11"]

    url = generate_google_flights_url(template_3seg, new_dates)

    assert "tfs=" in url
    assert url.startswith("https://www.google.com/travel/flights")
