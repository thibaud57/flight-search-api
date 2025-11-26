"""Parser pour extraire vols depuis JSON API interne Kayak."""

import logging
from typing import Any

from app.models import GoogleFlightDTO

logger = logging.getLogger(__name__)


def format_duration(minutes: int) -> str:
    """Convertit durée en minutes vers format 'Xh Ymin'."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}min"


class KayakFlightParser:
    """Parser pour extraire vols depuis JSON API interne Kayak."""

    def parse(self, json_data: dict[str, Any]) -> list[GoogleFlightDTO]:
        """Parse JSON Kayak et retourne liste vols au format GoogleFlightDTO."""
        if "results" not in json_data:
            raise ValueError("Missing 'results' key in Kayak JSON")
        if "legs" not in json_data:
            raise ValueError("Missing 'legs' key in Kayak JSON")
        if "segments" not in json_data:
            raise ValueError("Missing 'segments' key in Kayak JSON")

        results_data: list[dict[str, Any]] = json_data["results"]
        legs_data: dict[str, Any] = json_data["legs"]
        segments_data: dict[str, Any] = json_data["segments"]

        flights: list[GoogleFlightDTO] = []

        for result in results_data:
            price: float = result["price"]
            leg_ids: list[str] = result.get("legs", [])

            for leg_id in leg_ids:
                if leg_id not in legs_data:
                    logger.warning(
                        "Leg ID not found in legs dict",
                        extra={"leg_id": leg_id, "result_id": result.get("resultId")},
                    )
                    continue

                leg = legs_data[leg_id]
                duration_minutes: int = leg.get("duration", 0)
                stops: int = leg.get("stops", 0)
                segment_ids: list[str] = leg.get("segments", [])

                for segment_id in segment_ids:
                    if segment_id not in segments_data:
                        logger.warning(
                            "Segment ID not found in segments dict",
                            extra={
                                "segment_id": segment_id,
                                "leg_id": leg_id,
                            },
                        )
                        continue

                    segment = segments_data[segment_id]

                    flight = GoogleFlightDTO(
                        price=price,
                        airline=segment.get("airline", ""),
                        departure_time=segment.get("departure", ""),
                        arrival_time=segment.get("arrival", ""),
                        duration=format_duration(duration_minutes),
                        stops=stops,
                        departure_airport=segment.get("origin"),
                        arrival_airport=segment.get("destination"),
                    )
                    flights.append(flight)

        return sorted(flights, key=lambda f: f.price)
