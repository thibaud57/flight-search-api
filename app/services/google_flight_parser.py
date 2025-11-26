"""Parser de vols Google Flights avec JsonCssExtractionStrategy + aria-label."""

import json
import logging
import re
from typing import Any

from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from pydantic import ValidationError

from app.exceptions import ParsingError
from app.models.google_flight_dto import GoogleFlightDTO

logger = logging.getLogger(__name__)

PRICE_PATTERN = re.compile(r"(\d+(?:\s?\d+)*)\s*euros")
AIRLINE_PATTERN = re.compile(r"avec\s+([^.,]+)")
DEPARTURE_TIME_PATTERN = re.compile(r"Départ.*?(\d{1,2}:\d{2})")
ARRIVAL_TIME_PATTERN = re.compile(r"arrivée.*?(\d{1,2}:\d{2})")
DURATION_PATTERN = re.compile(r"Durée totale\s*:\s*(.+?)(?:\.|$)")
STOPS_PATTERN = re.compile(r"(\d+)\s*escales?")
DEPARTURE_AIRPORT_PATTERN = re.compile(r"Départ de ([^à]+) à")
ARRIVAL_AIRPORT_PATTERN = re.compile(r"arrivée à ([^à]+) à")

FLIGHT_SCHEMA = {
    "name": "Google Flights Results",
    "baseSelector": "li.pIav2d",
    "fields": [
        {
            "name": "aria_label",
            "selector": "div[aria-label]",
            "type": "attribute",
            "attribute": "aria-label",
        }
    ],
}


class GoogleFlightParser:
    """Parser de vols Google Flights avec JsonCssExtractionStrategy + aria-label."""

    def __init__(self) -> None:
        """Initialise avec stratégie Crawl4AI."""
        self._strategy = JsonCssExtractionStrategy(FLIGHT_SCHEMA)

    def parse(self, html: str) -> list[GoogleFlightDTO]:
        """Extrait les vols depuis HTML Google Flights."""
        raw_results = self._strategy.extract(url="", html_content=html)

        if not raw_results:
            logger.warning(
                "No flight containers found",
                extra={"html_size": len(html), "selector": "li.pIav2d"},
            )
            raise ParsingError(
                "No flights found in HTML", html_size=len(html), flights_found=0
            )

        flights: list[GoogleFlightDTO] = []
        skipped_no_aria_label = 0
        skipped_parse_failed = 0

        for raw_flight in raw_results:
            aria_label = raw_flight.get("aria_label")
            if not aria_label:
                skipped_no_aria_label += 1
                continue

            flight = self._parse_aria_label(aria_label)
            if flight:
                flights.append(flight)
            else:
                skipped_parse_failed += 1

        logger.info(
            "Parse iteration completed",
            extra={
                "total_raw_results": len(raw_results),
                "skipped_no_aria_label": skipped_no_aria_label,
                "skipped_parse_failed": skipped_parse_failed,
                "valid_flights": len(flights),
            },
        )

        if not flights:
            raise ParsingError(
                "Zero valid flights extracted",
                html_size=len(html),
                flights_found=0,
            )

        return flights

    def _parse_aria_label(self, aria_label: str) -> GoogleFlightDTO | None:
        """Parse un vol depuis aria-label."""
        try:
            price = self._extract_price(aria_label)
            airline = self._extract_airline(aria_label)
            departure_time = self._extract_time(aria_label, DEPARTURE_TIME_PATTERN)
            arrival_time = self._extract_time(aria_label, ARRIVAL_TIME_PATTERN)
            duration = self._extract_duration(aria_label)
            stops = self._extract_stops(aria_label)
            departure_airport = self._extract_airport(
                aria_label, DEPARTURE_AIRPORT_PATTERN
            )
            arrival_airport = self._extract_airport(aria_label, ARRIVAL_AIRPORT_PATTERN)

            if (
                price is None
                or airline is None
                or departure_time is None
                or arrival_time is None
            ):
                return None

            return GoogleFlightDTO(
                price=price,
                airline=airline,
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration=duration or "",
                stops=stops,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
            )
        except ValidationError as e:
            logger.warning(
                "Pydantic validation failed",
                extra={"error": str(e), "aria_label_preview": aria_label[:100]},
            )
            return None
        except Exception as e:
            logger.warning(
                "Unexpected parsing error",
                extra={"error": str(e), "aria_label_preview": aria_label[:100]},
            )
            return None

    def _extract_price(self, text: str) -> float | None:
        """Extrait prix depuis 'À partir de 1270 euros'."""
        match = PRICE_PATTERN.search(text)
        if not match:
            return None

        price_str = match.group(1).replace(" ", "")
        try:
            return float(price_str)
        except ValueError:
            return None

    def _extract_airline(self, text: str) -> str | None:
        """Extrait compagnie depuis 'avec ANA' ou 'avec Lufthansa, 1 escale'."""
        match = AIRLINE_PATTERN.search(text)
        return match.group(1).strip() if match else None

    def _extract_time(self, text: str, pattern: re.Pattern[str]) -> str | None:
        """Extrait heure depuis aria-label avec pattern donné."""
        match = pattern.search(text)
        return match.group(1) if match else None

    def _extract_duration(self, text: str) -> str | None:
        """Extrait durée depuis 'Durée totale : 13 h 40 min'."""
        match = DURATION_PATTERN.search(text)
        return match.group(1).strip() if match else None

    def _extract_stops(self, text: str) -> int | None:
        """Extrait escales depuis 'Vol direct' ou '1 escale'."""
        text_lower = text.lower()

        if "vol direct" in text_lower:
            return 0

        match = STOPS_PATTERN.search(text_lower)
        return int(match.group(1)) if match else None

    def _extract_airport(self, text: str, pattern: re.Pattern[str]) -> str | None:
        """Extrait aéroport depuis aria-label avec pattern donné."""
        match = pattern.search(text)
        return match.group(1).strip() if match else None

    def parse_api_responses(
        self, api_responses: list[dict[str, Any]]
    ) -> tuple[float, list[GoogleFlightDTO]]:
        """Parse JSON API responses pour extraire tous segments vols."""
        for response in api_responses:
            try:
                body = response.get("response_data") or response.get("body")
                if not body:
                    continue

                data = json.loads(body)

                if "data" not in data or "flights" not in data["data"]:
                    continue

                flights_data = data["data"]["flights"]
                if not flights_data or len(flights_data) == 0:
                    continue

                best_flight = flights_data[0]

                total_price = best_flight.get("price", {}).get("total")
                if total_price is None:
                    logger.error(
                        "Missing total price in JSON",
                        extra={"flight_id": best_flight.get("id")},
                    )
                    raise ParsingError("Missing total price in flight combination")

                segments = best_flight.get("segments", [])
                if not segments:
                    continue

                flights = []
                for segment in segments:
                    flight_dto = self._parse_segment(segment)
                    if flight_dto:
                        flights.append(flight_dto)

                if flights:
                    logger.info(
                        "Segments parsed from JSON",
                        extra={"segments_count": len(flights)},
                    )
                    logger.debug(
                        "First and last flight DTO",
                        extra={
                            "first_flight": {
                                "airline": flights[0].airline,
                                "departure": flights[0].departure_time,
                            },
                            "last_flight": {
                                "airline": flights[-1].airline,
                                "departure": flights[-1].departure_time,
                            }
                            if len(flights) > 1
                            else None,
                        },
                    )
                    return (total_price, flights)

            except json.JSONDecodeError as e:
                logger.error(
                    "JSON decode error",
                    extra={"error": str(e), "response_preview": str(body)[:100]},
                )
                continue
            except Exception as e:
                logger.error(
                    "Unexpected parsing error",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )
                continue

        raise ParsingError("No valid flight data found in API responses")

    def _parse_segment(self, segment: dict[str, Any]) -> GoogleFlightDTO | None:
        """Parse un segment JSON vers GoogleFlightDTO."""
        try:
            carrier = segment.get("carrier", {})
            airline = carrier.get("name", "Unknown")

            departure = segment.get("departure", {})
            arrival = segment.get("arrival", {})

            departure_time = self._format_time(departure.get("time", ""))
            arrival_time = self._format_time(arrival.get("time", ""))

            duration_minutes = segment.get("duration_minutes", 0)
            duration = self._format_duration(duration_minutes)

            stops = segment.get("stops", 0)

            departure_airport = departure.get("city") or departure.get("airport")
            arrival_airport = arrival.get("city") or arrival.get("airport")

            return GoogleFlightDTO(
                price=None,
                airline=airline,
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration=duration,
                stops=stops,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
            )
        except ValidationError as e:
            logger.warning(
                "Pydantic validation failed for segment", extra={"error": str(e)}
            )
            return None
        except Exception as e:
            logger.warning("Segment parsing failed", extra={"error": str(e)})
            return None

    def _format_time(self, iso_time: str) -> str:
        """Convertit ISO 8601 timestamp en HH:MM."""
        if not iso_time:
            return "Unknown"

        try:
            if "T" in iso_time:
                time_part = iso_time.split("T")[1]
                if ":" in time_part:
                    return time_part[:5]
        except Exception:
            pass

        return iso_time

    def _format_duration(self, duration_minutes: int) -> str:
        """Convertit minutes en format 'Xh XXmin'."""
        if duration_minutes == 0:
            return "Unknown"

        hours = duration_minutes // 60
        minutes = duration_minutes % 60

        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes:02d}min"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}min"
