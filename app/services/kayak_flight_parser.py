"""Parser pour extraire vols depuis JSON API interne Kayak."""

from typing import Any

from app.core.logger import get_logger
from app.models import KayakFlightDTO, LayoverInfo

logger = get_logger()


def format_duration(minutes: int) -> str:
    """Convertit durée en minutes vers format 'Xh Ymin'."""
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}min"


class KayakFlightParser:
    """Parser pour extraire vols depuis JSON API interne Kayak."""

    def parse(self, json_data: dict[str, Any]) -> list[KayakFlightDTO]:
        """Parse JSON Kayak et retourne liste vols au format KayakFlightDTO."""
        if "results" not in json_data:
            raise ValueError("Missing 'results' key in Kayak JSON")
        if "legs" not in json_data:
            raise ValueError("Missing 'legs' key in Kayak JSON")
        if "segments" not in json_data:
            raise ValueError("Missing 'segments' key in Kayak JSON")

        results_data = json_data["results"]
        legs_data = json_data["legs"]
        segments_data = json_data["segments"]

        if not results_data:
            return []

        flights = []
        for result in results_data:
            flight = self._parse_result(result, legs_data, segments_data)
            if flight:
                flights.append(flight)

        return flights

    def _parse_result(
        self,
        result: dict[str, Any],
        legs_data: dict[str, Any],
        segments_data: dict[str, Any],
    ) -> KayakFlightDTO | None:
        """Parse un result vers KayakFlightDTO."""
        result_id = result.get("resultId", "unknown")
        booking_options = result.get("bookingOptions", [])
        if not booking_options:
            logger.warning(
                f"Result {result_id} has no booking options",
                extra={"result_id": result_id},
            )
            return None

        first_option = booking_options[0]
        price = first_option.get("displayPrice", {}).get("price")
        if not price:
            logger.warning(
                f"Result {result_id} has no price", extra={"result_id": result_id}
            )
            return None

        leg_farings = first_option.get("legFarings", [])
        if not leg_farings:
            logger.warning(
                f"Result {result_id} has no leg farings", extra={"result_id": result_id}
            )
            return None

        leg_id = leg_farings[0].get("legId")
        if not leg_id or leg_id not in legs_data:
            logger.warning(
                f"Leg ID '{leg_id}' not found in legs dict",
                extra={"result_id": result_id, "leg_id": leg_id},
            )
            return None

        leg = legs_data[leg_id]
        return self._parse_leg(leg, segments_data, float(price))

    def _parse_leg(
        self, leg: dict[str, Any], segments_data: dict[str, Any], price: float
    ) -> KayakFlightDTO | None:
        """Parse un leg vers KayakFlightDTO."""
        leg_segments = leg.get("segments", [])
        if not leg_segments:
            return None

        segment_ids = [seg["id"] for seg in leg_segments]
        first_segment_id = segment_ids[0]
        last_segment_id = segment_ids[-1]

        if first_segment_id not in segments_data:
            logger.warning(
                f"Segment ID '{first_segment_id}' not found in segments dict",
                extra={"segment_id": first_segment_id},
            )
            return None

        if last_segment_id not in segments_data:
            logger.warning(
                f"Segment ID '{last_segment_id}' not found in segments dict",
                extra={"segment_id": last_segment_id},
            )
            return None

        first_segment = segments_data[first_segment_id]
        last_segment = segments_data[last_segment_id]

        layovers = self._extract_layovers(leg_segments, segments_data)

        duration_minutes = leg.get("duration", 0)
        duration_str = format_duration(duration_minutes)

        airline = first_segment.get("airline", "Unknown")
        departure_time = first_segment.get("departure", "")
        arrival_time = last_segment.get("arrival", "")
        departure_airport = first_segment.get("origin")
        arrival_airport = last_segment.get("destination")

        return KayakFlightDTO(
            price=price,
            airline=airline,
            departure_time=departure_time,
            arrival_time=arrival_time,
            duration=duration_str,
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            layovers=layovers,
        )

    def _extract_layovers(
        self, leg_segments: list[dict[str, Any]], segments_data: dict[str, Any]
    ) -> list[LayoverInfo]:
        """Extrait les layovers depuis les segments d'un leg."""
        layovers = []
        for i, seg_info in enumerate(leg_segments[:-1]):
            layover_data = seg_info.get("layover")
            if layover_data and "duration" in layover_data:
                layover_duration_minutes = layover_data["duration"]
                layover_duration_str = format_duration(layover_duration_minutes)

                next_segment_id = leg_segments[i + 1]["id"]
                if next_segment_id in segments_data:
                    next_segment = segments_data[next_segment_id]
                    layover_airport = next_segment.get("origin")
                    if layover_airport:
                        layovers.append(
                            LayoverInfo(
                                airport=layover_airport, duration=layover_duration_str
                            )
                        )
        return layovers
