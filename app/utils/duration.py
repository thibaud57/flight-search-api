"""Utilitaires de manipulation de durées au format HH:MM."""

from app.core.constants import DURATION_PATTERN_HHMM


def format_duration(minutes: int) -> str:
    """Convertit durée en minutes vers format HH:MM."""
    if minutes < 0 or minutes >= 6000:
        raise ValueError(
            f"Minutes must be between 0 and 5999 (99h59 max), got {minutes}"
        )

    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours:02d}:{remaining_minutes:02d}"


def parse_duration(duration_str: str) -> int:
    """Convertit format HH:MM vers minutes."""
    if not DURATION_PATTERN_HHMM.match(duration_str):
        raise ValueError(
            f"Invalid duration format. Expected HH:MM (zero-padded), got '{duration_str}'"
        )

    hours_str, minutes_str = duration_str.split(":")
    hours = int(hours_str)
    minutes = int(minutes_str)

    if hours > 99:
        raise ValueError(f"Hours must be <= 99, got {hours}")

    if minutes >= 60:
        raise ValueError(f"Minutes must be < 60, got {minutes}")

    return hours * 60 + minutes
