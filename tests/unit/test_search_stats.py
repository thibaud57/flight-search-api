import pytest
from pydantic import ValidationError

from app.models import SearchStats


def test_search_stats_creation(search_stats_factory):
    """Test création SearchStats valide."""
    stats = search_stats_factory()

    assert stats.total_results == 10
    assert stats.search_time_ms == 100
    assert stats.segments_count == 2


def test_search_stats_custom_values(search_stats_factory):
    """Test SearchStats avec valeurs personnalisées."""
    stats = search_stats_factory(
        total_results=25,
        search_time_ms=250,
        segments_count=3,
    )

    assert stats.total_results == 25
    assert stats.search_time_ms == 250
    assert stats.segments_count == 3


def test_search_stats_zero_results(search_stats_factory):
    """Test SearchStats accepte 0 résultats."""
    stats = search_stats_factory(total_results=0)

    assert stats.total_results == 0


def test_search_stats_required_fields():
    """Test SearchStats échoue sans champs requis."""
    with pytest.raises(ValidationError) as exc_info:
        SearchStats(total_results=10)

    error_str = str(exc_info.value)
    assert "search_time_ms" in error_str
    assert "segments_count" in error_str


def test_search_stats_extra_forbid(search_stats_factory):
    """Test SearchStats rejette champs extra."""
    with pytest.raises(ValidationError) as exc_info:
        SearchStats(
            total_results=10,
            search_time_ms=100,
            segments_count=2,
            extra_field="invalid",
        )

    assert "Extra inputs are not permitted" in str(exc_info.value)


def test_search_stats_serialization(search_stats_factory):
    """Test SearchStats sérialisation JSON."""
    stats = search_stats_factory(
        total_results=15,
        search_time_ms=120,
        segments_count=3,
    )

    json_data = stats.model_dump()

    assert json_data == {
        "total_results": 15,
        "search_time_ms": 120,
        "segments_count": 3,
    }


def test_search_stats_deserialization():
    """Test SearchStats désérialisation depuis dict."""
    data = {
        "total_results": 20,
        "search_time_ms": 150,
        "segments_count": 4,
    }

    stats = SearchStats(**data)

    assert stats.total_results == 20
    assert stats.search_time_ms == 150
    assert stats.segments_count == 4
