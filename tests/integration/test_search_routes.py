"""Tests integration routes search HTTP."""

import pytest
from fastapi.testclient import TestClient

from tests.fixtures.helpers import (
    GOOGLE_FLIGHT_TEMPLATE_URL,
    KAYAK_TEMPLATE_URL,
    SEARCH_GOOGLE_FLIGHTS_ENDPOINT,
    SEARCH_KAYAK_ENDPOINT,
)


def test_search_google_flights_returns_200_with_valid_request(
    client_with_mock_search: TestClient, google_search_request_factory
) -> None:
    """Request valide retourne 200 avec SearchResponse triee par prix."""
    request_data = google_search_request_factory(
        days_segment1=6, days_segment2=5, as_dict=True
    )

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert "search_stats" in data
    assert len(data["results"]) == 10
    assert data["search_stats"]["total_results"] == 10
    assert data["search_stats"]["segments_count"] == 2
    assert data["search_stats"]["search_time_ms"] > 0

    for i in range(len(data["results"]) - 1):
        assert (
            data["results"][i]["flights"][0]["price"]
            <= data["results"][i + 1]["flights"][0]["price"]
        )


@pytest.mark.parametrize(
    "segments_data,description",
    [
        ([], "segments vide"),
        (
            lambda factory: [
                factory(start_offset=10, duration=-10, as_dict=True),
                factory(start_offset=14, duration=5, as_dict=True),
            ],
            "dates invalides",
        ),
        (
            lambda factory: [
                factory(start_offset=1 + i * 10, duration=2, as_dict=True)
                for i in range(6)
            ],
            "trop de segments",
        ),
    ],
)
def test_search_google_flights_validation_errors_422(
    client_with_mock_search: TestClient,
    date_range_factory,
    segments_data,
    description,
) -> None:
    """Requetes invalides retournent 422."""
    if callable(segments_data):
        segments_data = segments_data(date_range_factory)

    request_data = {
        "template_url": GOOGLE_FLIGHT_TEMPLATE_URL,
        "segments_date_ranges": segments_data,
    }

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_search_google_flights_exact_dates_accepted(
    client_with_mock_search: TestClient, date_range_factory
) -> None:
    """Request avec dates exactes (start=end) retourne 200."""
    request_data = {
        "template_url": GOOGLE_FLIGHT_TEMPLATE_URL,
        "segments_date_ranges": [
            date_range_factory(start_offset=1, duration=0, as_dict=True),
            date_range_factory(start_offset=6, duration=0, as_dict=True),
        ],
    }

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == 10
    assert data["search_stats"]["segments_count"] == 2


def test_search_google_flights_extra_field_rejected(
    client_with_mock_search: TestClient, google_search_request_factory
) -> None:
    """SearchRequest avec champ extra doit etre rejete (extra=forbid)."""
    request_data = google_search_request_factory(as_dict=True)
    request_data["provider"] = "google_flights"

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any(
        "extra" in str(err).lower() or "forbidden" in str(err).lower()
        for err in error_detail
    )


def test_search_kayak_returns_200_with_valid_request(
    client_with_mock_search: TestClient, kayak_search_request_factory
) -> None:
    """Request valide retourne 200 avec SearchResponse triee par prix."""
    request_data = kayak_search_request_factory(
        days_segment1=6, days_segment2=5, as_dict=True
    )

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert "search_stats" in data
    assert len(data["results"]) == 10
    assert data["search_stats"]["total_results"] == 10
    assert data["search_stats"]["segments_count"] == 2
    assert data["search_stats"]["search_time_ms"] > 0

    for i in range(len(data["results"]) - 1):
        assert (
            data["results"][i]["flights"][0]["price"]
            <= data["results"][i + 1]["flights"][0]["price"]
        )


@pytest.mark.parametrize(
    "segments_data,description",
    [
        ([], "segments vide"),
        (
            lambda factory: [
                factory(start_offset=10, duration=-10, as_dict=True),
                factory(start_offset=14, duration=5, as_dict=True),
            ],
            "dates invalides",
        ),
        (
            lambda factory: [
                factory(start_offset=1 + i * 10, duration=2, as_dict=True)
                for i in range(7)
            ],
            "trop de segments",
        ),
    ],
)
def test_search_kayak_validation_errors_422(
    client_with_mock_search: TestClient,
    date_range_factory,
    segments_data,
    description,
) -> None:
    """Requetes invalides retournent 422."""
    if callable(segments_data):
        segments_data = segments_data(date_range_factory)

    request_data = {
        "template_url": KAYAK_TEMPLATE_URL,
        "segments_date_ranges": segments_data,
    }

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_search_kayak_exact_dates_accepted(
    client_with_mock_search: TestClient, date_range_factory
) -> None:
    """Request avec dates exactes (start=end) retourne 200."""
    request_data = {
        "template_url": KAYAK_TEMPLATE_URL,
        "segments_date_ranges": [
            date_range_factory(start_offset=1, duration=0, as_dict=True),
            date_range_factory(start_offset=6, duration=0, as_dict=True),
        ],
    }

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == 10
    assert data["search_stats"]["segments_count"] == 2


def test_search_kayak_extra_field_rejected(
    client_with_mock_search: TestClient, kayak_search_request_factory
) -> None:
    """SearchRequest avec champ extra doit etre rejete (extra=forbid)."""
    request_data = kayak_search_request_factory(as_dict=True)
    request_data["provider"] = "kayak"

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any(
        "extra" in str(err).lower() or "forbidden" in str(err).lower()
        for err in error_detail
    )


@pytest.mark.parametrize(
    "endpoint,template_url",
    [
        (SEARCH_GOOGLE_FLIGHTS_ENDPOINT, GOOGLE_FLIGHT_TEMPLATE_URL),
        (SEARCH_KAYAK_ENDPOINT, KAYAK_TEMPLATE_URL),
    ],
)
def test_search_both_providers_validation_empty_segments_422(
    client_with_mock_search: TestClient,
    endpoint,
    template_url,
) -> None:
    """Les 2 endpoints valident segments vide et retournent 422."""
    request_data = {
        "template_url": template_url,
        "segments_date_ranges": [],
    }

    response = client_with_mock_search.post(endpoint, json=request_data)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_old_route_search_flights_returns_404(
    client_with_mock_search: TestClient, google_search_request_factory
) -> None:
    """Ancienne route /search-flights retourne 404."""
    request_data = google_search_request_factory(as_dict=True)

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 404


def test_openapi_schema_includes_search_endpoints(
    client_with_mock_search: TestClient,
) -> None:
    """OpenAPI schema contient endpoints search."""
    response = client_with_mock_search.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    assert "paths" in schema
    assert SEARCH_GOOGLE_FLIGHTS_ENDPOINT in schema["paths"]
    assert SEARCH_KAYAK_ENDPOINT in schema["paths"]

    google_endpoint = schema["paths"][SEARCH_GOOGLE_FLIGHTS_ENDPOINT]
    assert "post" in google_endpoint
    assert "requestBody" in google_endpoint["post"]
    assert "responses" in google_endpoint["post"]


def test_search_google_flights_network_error_returns_502(
    client_with_network_error: TestClient, google_search_request_factory
) -> None:
    """NetworkError retourne 502 Bad Gateway avec message structuré."""
    request_data = google_search_request_factory(as_dict=True)

    response = client_with_network_error.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 502
    data = response.json()
    assert "detail" in data
    assert "attempts" in data
    assert "failed to fetch" in data["detail"].lower()


def test_search_google_flights_session_error_returns_503(
    client_with_session_error: TestClient, google_search_request_factory
) -> None:
    """SessionCaptureError retourne 503 Service Unavailable avec raison."""
    request_data = google_search_request_factory(as_dict=True)

    response = client_with_session_error.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "reason" in data
    assert "failed to establish session" in data["detail"].lower()
    assert "google" in data["detail"].lower()


def test_search_google_flights_captcha_error_returns_503(
    client_with_captcha_error: TestClient, google_search_request_factory
) -> None:
    """CaptchaDetectedError retourne 503 Service Unavailable avec type captcha."""
    request_data = google_search_request_factory(as_dict=True)

    response = client_with_captcha_error.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "captcha_type" in data
    assert "captcha" in data["detail"].lower()
    assert data["captcha_type"] == "recaptcha"


def test_search_kayak_network_error_returns_502(
    client_with_network_error: TestClient, kayak_search_request_factory
) -> None:
    """NetworkError retourne 502 Bad Gateway pour Kayak."""
    request_data = kayak_search_request_factory(as_dict=True)

    response = client_with_network_error.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 502
    data = response.json()
    assert "detail" in data
    assert "attempts" in data


def test_search_kayak_session_error_returns_503(
    client_with_session_error: TestClient, kayak_search_request_factory
) -> None:
    """SessionCaptureError retourne 503 Service Unavailable pour Kayak."""
    request_data = kayak_search_request_factory(as_dict=True)

    response = client_with_session_error.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "reason" in data


def test_search_kayak_captcha_error_returns_503(
    client_with_captcha_error: TestClient, kayak_search_request_factory
) -> None:
    """CaptchaDetectedError retourne 503 Service Unavailable pour Kayak."""
    request_data = kayak_search_request_factory(as_dict=True)

    response = client_with_captcha_error.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 503
    data = response.json()
    assert "detail" in data
    assert "captcha_type" in data
    assert data["captcha_type"] == "recaptcha"


def test_search_kayak_with_filters_returns_200_filtered(
    client_with_mock_search: TestClient, kayak_search_request_factory
) -> None:
    """POST avec filters dans date_range retourne 200 avec vols filtres."""
    request_data = kayak_search_request_factory(as_dict=True)
    request_data["segments_date_ranges"][0]["filters"] = {
        "max_duration": "12:00",
        "max_stops": 1,
    }

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data


def test_search_kayak_with_invalid_filter_format_returns_422(
    client_with_mock_search: TestClient, kayak_search_request_factory
) -> None:
    """POST filters format invalide retourne 422 ValidationError."""
    request_data = kayak_search_request_factory(as_dict=True)
    request_data["segments_date_ranges"][0]["filters"] = {
        "max_duration": "invalid_format",
    }

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("duration" in str(err).lower() for err in error_detail)


def test_search_kayak_without_filters_backward_compatible(
    client_with_mock_search: TestClient, kayak_search_request_factory
) -> None:
    """POST sans filters backward compatible retourne 200."""
    request_data = kayak_search_request_factory(as_dict=True)

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 10


def test_search_kayak_layover_range_invalid_returns_422(
    client_with_mock_search: TestClient, kayak_search_request_factory
) -> None:
    """POST layover range invalide retourne 422 ValidationError."""
    request_data = kayak_search_request_factory(as_dict=True)
    request_data["segments_date_ranges"][0]["filters"] = {
        "min_layover_duration": "05:00",
        "max_layover_duration": "03:00",
    }

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("layover" in str(err).lower() for err in error_detail)
