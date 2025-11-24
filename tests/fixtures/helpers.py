"""Helper functions pour assertions répétées et utilitaires dates."""

from datetime import date, timedelta

TEMPLATE_URL = "https://www.google.com/travel/flights?tfs=test"


def get_future_date(days_offset: int = 1) -> date:
    """Retourne date future avec offset depuis aujourd'hui."""
    return date.today() + timedelta(days=days_offset)


def get_past_date(days_offset: int = 1) -> date:
    """Retourne date passée avec offset depuis aujourd'hui."""
    return date.today() - timedelta(days=abs(days_offset))


def get_date_range(
    start_offset: int, duration: int, past: bool = False
) -> tuple[date, date]:
    """Retourne (start_date, end_date) pour range."""
    start = get_past_date(start_offset) if past else get_future_date(start_offset)
    end = start + timedelta(days=duration)
    return start, end


def assert_search_response_valid(response, min_results=0):
    """Helper assertions pour valider SearchResponse structure."""
    from app.models.response import SearchResponse

    assert isinstance(response, SearchResponse)
    assert len(response.results) >= min_results
    assert response.search_stats.total_results >= min_results
    if len(response.results) > 0:
        assert response.results[0].flights[0].price > 0
