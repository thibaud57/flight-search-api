"""Tests unitaires NetworkResponseFilter."""

import pytest

from app.services.network_response_filter import NetworkResponseFilter


@pytest.fixture
def network_filter():
    """NetworkResponseFilter instance."""
    return NetworkResponseFilter()


def test_filter_keeps_response_events_only(network_filter):
    """Filtre garde seulement event_type=response."""
    events = [
        {"event_type": "request", "url": "https://google.com"},
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {"event_type": "request", "url": "https://google.com"},
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {"event_type": "request_failed", "url": "https://google.com"},
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "fetch",
            "response_data": "{}",
        },
        {"event_type": "request", "url": "https://google.com"},
        {"event_type": "request", "url": "https://google.com"},
        {"event_type": "request_failed", "url": "https://google.com"},
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "body": "{}",
        },
    ]

    result = network_filter.filter_flight_api_responses(events)

    assert len(result) == 4
    assert all(e["event_type"] == "response" for e in result)


def test_filter_requires_status_200(network_filter):
    """Filtre garde seulement status 200."""
    events = [
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 404,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 500,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
    ]

    result = network_filter.filter_flight_api_responses(events)

    assert len(result) == 3
    assert all(e["status"] == 200 for e in result)


def test_filter_requires_xhr_fetch_resource_type(network_filter):
    """Filtre garde seulement XHR/Fetch."""
    events = [
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "fetch",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "image",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "script",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "fetch",
            "response_data": "{}",
        },
    ]

    result = network_filter.filter_flight_api_responses(events)

    assert len(result) == 4
    assert all(e["resource_type"] in ["xhr", "fetch"] for e in result)


def test_filter_requires_google_domain(network_filter):
    """Filtre garde seulement URLs google.com."""
    events = [
        {
            "event_type": "response",
            "url": "https://www.google.com/travel/flights/rpc/search",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://googleapis.com/api/data",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://www.google.com/travel/filters",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
        {
            "event_type": "response",
            "url": "https://thirdparty.com/analytics",
            "status": 200,
            "resource_type": "xhr",
            "response_data": "{}",
        },
    ]

    result = network_filter.filter_flight_api_responses(events)

    assert len(result) == 2
    assert all("google.com" in e["url"] for e in result)


def test_filter_requires_response_body_present(network_filter):
    """Filtre exclut events sans body."""
    events = [
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "response_data": '{"data": "value"}',
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
        },
        {
            "event_type": "response",
            "url": "https://google.com",
            "status": 200,
            "resource_type": "xhr",
            "body": '{"data": "value"}',
        },
    ]

    result = network_filter.filter_flight_api_responses(events)

    assert len(result) == 2
    assert all("response_data" in e or "body" in e for e in result)


def test_filter_returns_empty_if_no_match(network_filter):
    """Retourne liste vide si aucun match."""
    events = [
        {"event_type": "request", "url": "https://google.com"},
        {"event_type": "request", "url": "https://google.com"},
        {"event_type": "response", "url": "https://google.com", "status": 404},
        {"event_type": "request_failed", "url": "https://google.com"},
        {"event_type": "request", "url": "https://google.com"},
    ]

    result = network_filter.filter_flight_api_responses(events)

    assert result == []
    assert isinstance(result, list)
