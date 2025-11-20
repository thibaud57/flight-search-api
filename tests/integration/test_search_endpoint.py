from datetime import date, timedelta


def test_end_to_end_search_request_valid(client):
    """Test intégration 1: Request valide retourne 200 avec SearchResponse."""
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

    response = client.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert "search_stats" in data

    assert len(data["results"]) == 10

    for i in range(len(data["results"]) - 1):
        assert data["results"][i]["price"] <= data["results"][i + 1]["price"]

    assert data["search_stats"]["total_results"] == 10
    assert data["search_stats"]["segments_count"] == 2
    assert data["search_stats"]["search_time_ms"] > 0


def test_end_to_end_validation_error_empty_segments(client):
    """Test intégration 2: Segments vide retourne 422."""
    request_data = {"segments": []}

    response = client.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 422

    data = response.json()
    assert "detail" in data


def test_end_to_end_validation_error_invalid_dates(client):
    """Test intégration 3: Dates invalides retourne 422."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": (tomorrow + timedelta(days=10)).isoformat(),
                    "end": tomorrow.isoformat(),
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

    response = client.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 422

    data = response.json()
    assert "detail" in data


def test_end_to_end_search_request_exact_dates(client):
    """Test intégration 4: Request avec dates exactes (start=end) retourne 200."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Rio",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": tomorrow.isoformat(),
                },
            },
            {
                "from_city": "Buenos Aires",
                "to_city": "Santiago",
                "date_range": {
                    "start": (tomorrow + timedelta(days=6)).isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Santiago",
                "to_city": "Paris",
                "date_range": {
                    "start": (tomorrow + timedelta(days=8)).isoformat(),
                    "end": (tomorrow + timedelta(days=8)).isoformat(),
                },
            },
        ]
    }

    response = client.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 10
    assert data["search_stats"]["segments_count"] == 3


def test_end_to_end_openapi_schema_includes_endpoint(client):
    """Test intégration 5: OpenAPI schema contient endpoint search-flights."""
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/search-flights" in schema["paths"]

    endpoint = schema["paths"]["/api/v1/search-flights"]
    assert "post" in endpoint

    post_spec = endpoint["post"]
    assert "requestBody" in post_spec
    assert "responses" in post_spec
