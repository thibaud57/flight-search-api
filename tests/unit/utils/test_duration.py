"""Tests unitaires pour utilitaires duration."""

import pytest

from app.utils.duration import format_duration, parse_duration


class TestFormatDuration:
    """Tests pour format_duration."""

    def test_format_duration_150_minutes(self) -> None:
        """Devrait convertir 150 minutes en 02:30."""
        result = format_duration(150)

        assert result == "02:30"

    def test_format_duration_60_minutes(self) -> None:
        """Devrait convertir 60 minutes en 01:00."""
        result = format_duration(60)

        assert result == "01:00"

    def test_format_duration_0_minutes(self) -> None:
        """Devrait convertir 0 minutes en 00:00."""
        result = format_duration(0)

        assert result == "00:00"

    def test_format_duration_1439_minutes_max_edge_case(self) -> None:
        """Devrait convertir 1439 minutes (23h59) en 23:59."""
        result = format_duration(1439)

        assert result == "23:59"

    def test_format_duration_negative_raises_error(self) -> None:
        """Devrait lever ValueError pour minutes négatives."""
        with pytest.raises(ValueError, match="Minutes must be between 0 and 5999"):
            format_duration(-1)

    def test_format_duration_6000_raises_error(self) -> None:
        """Devrait lever ValueError pour 6000 minutes (100h)."""
        with pytest.raises(ValueError, match="Minutes must be between 0 and 5999"):
            format_duration(6000)


class TestParseDuration:
    """Tests pour parse_duration."""

    def test_parse_duration_02_30(self) -> None:
        """Devrait convertir 02:30 en 150 minutes."""
        result = parse_duration("02:30")

        assert result == 150

    def test_parse_duration_01_00(self) -> None:
        """Devrait convertir 01:00 en 60 minutes."""
        result = parse_duration("01:00")

        assert result == 60

    def test_parse_duration_12_60_invalid_minutes(self) -> None:
        """Devrait lever ValueError pour minutes >= 60."""
        with pytest.raises(ValueError, match="Minutes must be < 60"):
            parse_duration("12:60")

    def test_parse_duration_2_30_invalid_format(self) -> None:
        """Devrait lever ValueError pour format non zero-padded."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration("2:30")

    def test_parse_duration_invalid_format_3_digits(self) -> None:
        """Devrait lever ValueError pour format avec 3 chiffres (hors pattern)."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration("100:00")
