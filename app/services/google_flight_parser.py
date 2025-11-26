"""Parser de vols Google Flights avec JsonCssExtractionStrategy + aria-label."""

import logging
import re

from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from pydantic import ValidationError

from app.exceptions import ParsingError
from app.models import GoogleFlightDTO

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
