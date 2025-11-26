"""Constructeur d'URLs Kayak multi-city."""

from app.models import KayakSegment


class KayakUrlBuilder:
    """Constructeur d'URLs Kayak multi-city."""

    def __init__(self, base_url: str = "https://www.kayak.fr") -> None:
        """Initialise builder avec URL de base."""
        self.base_url = base_url

    def build_url(self, segments: list[KayakSegment]) -> str:
        """Construit URL Kayak complete depuis segments."""
        if len(segments) == 0:
            raise ValueError("At least 1 segment required")

        if len(segments) > 6:
            raise ValueError("Maximum 6 segments allowed (Kayak limit)")

        path_parts = []
        for segment in segments:
            path_parts.append(f"{segment.origin}-{segment.destination}")
            path_parts.append(segment.date)

        path = "/".join(path_parts)
        return f"{self.base_url}/flights/{path}?sort=bestflight_a"
