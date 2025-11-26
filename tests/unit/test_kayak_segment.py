"""Tests unitaires pour KayakSegment."""

import pytest
from pydantic import ValidationError

from app.utils import KayakSegment


class TestKayakSegment:
    """Tests validation KayakSegment."""

    def test_segment_valid(self):
        """Segment valide avec codes uppercase."""
        # Arrange & Act
        segment = KayakSegment(origin="PAR", destination="TYO", date="2026-01-14")

        # Assert
        assert segment.origin == "PAR"
        assert segment.destination == "TYO"
        assert segment.date == "2026-01-14"

    def test_segment_invalid_origin_lowercase(self):
        """Code origine lowercase."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            KayakSegment(origin="par", destination="TYO", date="2026-01-14")

        assert "origin" in str(exc_info.value)

    def test_segment_invalid_origin_length(self):
        """Code origine trop long."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            KayakSegment(origin="PARIS", destination="TYO", date="2026-01-14")

        assert "origin" in str(exc_info.value)

    def test_segment_invalid_destination_empty(self):
        """Code destination vide."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            KayakSegment(origin="PAR", destination="", date="2026-01-14")

        assert "destination" in str(exc_info.value)

    def test_segment_invalid_date_format(self):
        """Date non ISO."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            KayakSegment(origin="PAR", destination="TYO", date="14/01/2026")

        assert "date" in str(exc_info.value)

    def test_segment_invalid_date_partial(self):
        """Date incomplète."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            KayakSegment(origin="PAR", destination="TYO", date="2026-01")

        assert "date" in str(exc_info.value)

    def test_segment_invalid_mixedcase_rejected(self):
        """Codes mixedcase rejetés."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            KayakSegment(origin="Par", destination="TYO", date="2026-01-14")

        with pytest.raises(ValidationError):
            KayakSegment(origin="PAR", destination="tyo", date="2026-01-14")

    def test_segment_valid_future_date(self):
        """Date future lointaine."""
        # Arrange & Act
        segment = KayakSegment(origin="PAR", destination="TYO", date="2030-12-31")

        # Assert
        assert segment.date == "2030-12-31"
