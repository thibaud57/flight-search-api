"""Tests unitaires endpoint search."""

from datetime import date, timedelta

# Note: mock_search_service et client_with_mock_search sont définis dans conftest.py


def test_endpoint_accepts_valid_request(client_with_mock_search):
    """Test 39: Endpoint accepte request valide."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Tokyo",
                "to_city": "New York",
                "date_range": {
                    "start": (tomorrow + timedelta(days=14)).isoformat(),
                    "end": (tomorrow + timedelta(days=19)).isoformat(),
                },
            },
        ]
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data


def test_endpoint_validates_request_body(client_with_mock_search):
    """Test 40: Body invalide rejete."""
    request_data = {"segments": []}

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_endpoint_returns_10_results(client_with_mock_search):
    """Test 41: Endpoint retourne 10 resultats."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Tokyo",
                "to_city": "New York",
                "date_range": {
                    "start": (tomorrow + timedelta(days=14)).isoformat(),
                    "end": (tomorrow + timedelta(days=19)).isoformat(),
                },
            },
        ]
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 10


def test_endpoint_response_matches_schema(client_with_mock_search):
    """Test 42: Response conforme SearchResponse schema."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Tokyo",
                "to_city": "New York",
                "date_range": {
                    "start": (tomorrow + timedelta(days=14)).isoformat(),
                    "end": (tomorrow + timedelta(days=19)).isoformat(),
                },
            },
        ]
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data

    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0

    first_result = data["results"][0]
    assert "price" in first_result
    assert "airline" in first_result
    assert "departure_date" in first_result
    assert "segments" in first_result

    stats = data["search_stats"]
    assert "total_results" in stats
    assert "search_time_ms" in stats
    assert "segments_count" in stats


def test_endpoint_injects_search_service_dependency(client_with_mock_search):
    """Test 43: SearchService injecte via Depends()."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Tokyo",
                "to_city": "New York",
                "date_range": {
                    "start": (tomorrow + timedelta(days=14)).isoformat(),
                    "end": (tomorrow + timedelta(days=19)).isoformat(),
                },
            },
        ]
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
