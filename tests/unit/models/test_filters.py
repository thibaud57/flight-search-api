"""Tests unitaires pour app/models/filters.py (SegmentFilters)."""

import pytest
from pydantic import ValidationError

from app.models.filters import SegmentFilters


class TestSegmentFiltersDurationValidation:
    """Tests validation format durée."""

    def test_max_duration_valid_format(self) -> None:
        """Devrait accepter max_duration au format HH:MM."""
        filters = SegmentFilters(max_duration="12:00")

        assert filters.max_duration == "12:00"

    def test_max_duration_valid_zero_padded(self) -> None:
        """Devrait accepter max_duration zero-padded."""
        filters = SegmentFilters(max_duration="02:30")

        assert filters.max_duration == "02:30"

    def test_max_duration_invalid_minutes_gte_60(self) -> None:
        """Devrait rejeter max_duration avec minutes >= 60."""
        with pytest.raises(ValidationError, match="Minutes must be < 60"):
            SegmentFilters(max_duration="12:60")

    def test_max_duration_invalid_not_zero_padded(self) -> None:
        """Devrait rejeter max_duration sans zero-padding."""
        with pytest.raises(ValidationError, match="Invalid duration format"):
            SegmentFilters(max_duration="2:30")

    def test_max_duration_invalid_exceeds_24h(self) -> None:
        """Devrait rejeter max_duration > 24h."""
        with pytest.raises(
            ValidationError, match="Max duration must be <= 1440 minutes"
        ):
            SegmentFilters(max_duration="25:00")

    def test_min_layover_duration_invalid_format(self) -> None:
        """Devrait rejeter min_layover_duration format invalide."""
        with pytest.raises(ValidationError, match="Invalid duration format"):
            SegmentFilters(min_layover_duration="invalid")


class TestSegmentFiltersMaxStops:
    """Tests validation max_stops."""

    def test_max_stops_zero_valid(self) -> None:
        """Devrait accepter max_stops=0 (vol direct uniquement)."""
        filters = SegmentFilters(max_stops=0)

        assert filters.max_stops == 0

    def test_max_stops_exceeds_3_invalid(self) -> None:
        """Devrait rejeter max_stops > 3."""
        with pytest.raises(ValidationError, match="Max stops must be between 0 and 3"):
            SegmentFilters(max_stops=4)


class TestSegmentFiltersLimitesDuree:
    """Tests validation limites durée."""

    def test_max_duration_24h_limit_valid(self) -> None:
        """Devrait accepter max_duration=24:00 (limite max)."""
        filters = SegmentFilters(max_duration="24:00")

        assert filters.max_duration == "24:00"

    def test_min_layover_duration_12h_limit_valid(self) -> None:
        """Devrait accepter min_layover_duration=12:00 (limite max 12h)."""
        filters = SegmentFilters(min_layover_duration="12:00")

        assert filters.min_layover_duration == "12:00"


class TestSegmentFiltersLayoverRange:
    """Tests validation layover range."""

    def test_layover_range_valid_max_gt_min(self) -> None:
        """Devrait accepter max > min (strictement)."""
        filters = SegmentFilters(
            min_layover_duration="01:30", max_layover_duration="06:00"
        )

        assert filters.min_layover_duration == "01:30"
        assert filters.max_layover_duration == "06:00"

    def test_layover_range_invalid_equal(self) -> None:
        """Devrait rejeter max == min."""
        with pytest.raises(
            ValidationError,
            match=r"max_layover_duration .* must be strictly greater than min_layover_duration",
        ):
            SegmentFilters(min_layover_duration="06:00", max_layover_duration="06:00")

    def test_layover_range_invalid_max_lt_min(self) -> None:
        """Devrait rejeter max < min (inversé)."""
        with pytest.raises(
            ValidationError,
            match=r"max_layover_duration .* must be strictly greater than min_layover_duration",
        ):
            SegmentFilters(min_layover_duration="06:00", max_layover_duration="01:30")

    def test_layover_range_valid_only_min_defined(self) -> None:
        """Devrait accepter un seul défini (min uniquement)."""
        filters = SegmentFilters(
            min_layover_duration="01:30", max_layover_duration=None
        )

        assert filters.min_layover_duration == "01:30"
        assert filters.max_layover_duration is None
