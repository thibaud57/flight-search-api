from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app


class TestSearchFlightsEndToEnd:
    def test_end_to_end_search_request_valid(self) -> None:
        client = TestClient(app)
        start = (date.today() + timedelta(days=1)).isoformat()
        end = (date.today() + timedelta(days=15)).isoformat()
        request_data = {
            "destinations": ["Paris", "Tokyo"],
            "date_range": {"start": start, "end": end},
        }

        response = client.post("/api/v1/search-flights", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "search_stats" in data
        assert len(data["results"]) == 10
        assert data["results"][0]["price"] < data["results"][9]["price"]

    def test_end_to_end_validation_error_empty_destinations(self) -> None:
        client = TestClient(app)
        start = (date.today() + timedelta(days=1)).isoformat()
        end = (date.today() + timedelta(days=15)).isoformat()
        request_data = {
            "destinations": [],
            "date_range": {"start": start, "end": end},
        }

        response = client.post("/api/v1/search-flights", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_end_to_end_validation_error_invalid_dates(self) -> None:
        client = TestClient(app)
        start = (date.today() + timedelta(days=15)).isoformat()
        end = (date.today() + timedelta(days=1)).isoformat()
        request_data = {
            "destinations": ["Paris"],
            "date_range": {"start": start, "end": end},
        }

        response = client.post("/api/v1/search-flights", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_end_to_end_openapi_schema_includes_endpoint(self) -> None:
        client = TestClient(app)

        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert "/api/v1/search-flights" in schema["paths"]
        assert "post" in schema["paths"]["/api/v1/search-flights"]
