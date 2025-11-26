"""Tests unitaires pour KayakUrlBuilder."""

import pytest

from app.utils import KayakSegment, KayakUrlBuilder


class TestKayakUrlBuilder:
    """Tests construction URLs Kayak."""

    def test_build_url_single_segment(self):
        """URL aller simple."""
        # Arrange
        builder = KayakUrlBuilder()
        segments = [KayakSegment(origin="PAR", destination="SLZ", date="2026-01-14")]

        # Act
        url = builder.build_url(segments)

        # Assert
        assert (
            url == "https://www.kayak.fr/flights/PAR-SLZ/2026-01-14?sort=bestflight_a"
        )

    def test_build_url_two_segments(self):
        """URL aller-retour."""
        # Arrange
        builder = KayakUrlBuilder()
        segments = [
            KayakSegment(origin="PAR", destination="TYO", date="2026-03-15"),
            KayakSegment(origin="TYO", destination="PAR", date="2026-03-25"),
        ]

        # Act
        url = builder.build_url(segments)

        # Assert
        expected = "https://www.kayak.fr/flights/PAR-TYO/2026-03-15/TYO-PAR/2026-03-25?sort=bestflight_a"
        assert url == expected

    def test_build_url_three_segments_multicity(self):
        """URL multi-city 3 segments."""
        # Arrange
        builder = KayakUrlBuilder()
        segments = [
            KayakSegment(origin="PAR", destination="SLZ", date="2026-01-14"),
            KayakSegment(origin="SLZ", destination="LIM", date="2026-03-28"),
            KayakSegment(origin="LIM", destination="PAR", date="2026-04-10"),
        ]

        # Act
        url = builder.build_url(segments)

        # Assert
        expected = "https://www.kayak.fr/flights/PAR-SLZ/2026-01-14/SLZ-LIM/2026-03-28/LIM-PAR/2026-04-10?sort=bestflight_a"
        assert url == expected

    def test_build_url_six_segments_max(self):
        """URL 6 segments (limite max)."""
        # Arrange
        builder = KayakUrlBuilder()
        segments = [
            KayakSegment(origin="PAR", destination="NYC", date="2026-01-01"),
            KayakSegment(origin="NYC", destination="LAX", date="2026-02-01"),
            KayakSegment(origin="LAX", destination="TYO", date="2026-03-01"),
            KayakSegment(origin="TYO", destination="BKK", date="2026-04-01"),
            KayakSegment(origin="BKK", destination="DXB", date="2026-05-01"),
            KayakSegment(origin="DXB", destination="PAR", date="2026-06-01"),
        ]

        # Act
        url = builder.build_url(segments)

        # Assert
        assert url.startswith("https://www.kayak.fr/flights/")
        assert url.endswith("?sort=bestflight_a")
        assert "PAR-NYC" in url
        assert "DXB-PAR" in url
        assert len(segments) == 6

    def test_build_url_empty_segments(self):
        """Liste segments vide."""
        # Arrange
        builder = KayakUrlBuilder()
        segments: list[KayakSegment] = []

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            builder.build_url(segments)

        assert "cannot be empty" in str(exc_info.value)

    def test_build_url_seven_segments_exceeds_limit(self):
        """Liste >6 segments."""
        # Arrange
        builder = KayakUrlBuilder()
        segments = [
            KayakSegment(origin="PAR", destination="NYC", date="2026-01-01"),
            KayakSegment(origin="NYC", destination="LAX", date="2026-02-01"),
            KayakSegment(origin="LAX", destination="TYO", date="2026-03-01"),
            KayakSegment(origin="TYO", destination="BKK", date="2026-04-01"),
            KayakSegment(origin="BKK", destination="DXB", date="2026-05-01"),
            KayakSegment(origin="DXB", destination="LHR", date="2026-06-01"),
            KayakSegment(origin="LHR", destination="PAR", date="2026-07-01"),
        ]

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            builder.build_url(segments)

        assert "maximum 6 segments" in str(exc_info.value)

    def test_build_url_custom_base_url(self):
        """Base URL personnalisée."""
        # Arrange
        builder = KayakUrlBuilder(base_url="https://www.kayak.com")
        segments = [KayakSegment(origin="PAR", destination="TYO", date="2026-01-14")]

        # Act
        url = builder.build_url(segments)

        # Assert
        assert url.startswith("https://www.kayak.com/flights/")
        assert url.endswith("?sort=bestflight_a")

    def test_build_url_sort_param_present(self):
        """Query param sort présent."""
        # Arrange
        builder = KayakUrlBuilder()
        segments = [KayakSegment(origin="PAR", destination="TYO", date="2026-01-14")]

        # Act
        url = builder.build_url(segments)

        # Assert
        assert url.endswith("?sort=bestflight_a")

    def test_build_url_segment_separator(self):
        """Séparateurs corrects."""
        # Arrange
        builder = KayakUrlBuilder()
        segments = [
            KayakSegment(origin="PAR", destination="TYO", date="2026-03-15"),
            KayakSegment(origin="TYO", destination="PAR", date="2026-03-25"),
        ]

        # Act
        url = builder.build_url(segments)

        # Assert
        assert "PAR-TYO" in url
        assert "TYO-PAR" in url
        assert "/2026-03-15/" in url
        assert "/2026-03-25" in url

    def test_build_url_no_trailing_slash(self):
        """Pas de slash final."""
        # Arrange
        builder = KayakUrlBuilder()
        segments = [KayakSegment(origin="PAR", destination="TYO", date="2026-01-14")]

        # Act
        url = builder.build_url(segments)

        # Assert
        assert url.endswith("2026-01-14?sort=bestflight_a")
        assert "2026-01-14/?sort" not in url
