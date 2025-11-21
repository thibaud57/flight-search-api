"""Parser de vols Google Flights via JsonCssExtractionStrategy."""

import logging
import re
from datetime import datetime
from typing import Any

from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from pydantic import ValidationError

from app.exceptions import ParsingError
from app.models.google_flight_dto import GoogleFlightDTO

logger = logging.getLogger(__name__)

EXTRACTION_SCHEMA: dict[str, object] = {
    "name": "Google Flights Data",
    "baseSelector": ".pIav2d",
    "fields": [
        {"name": "price", "selector": ".FpEdX", "type": "text"},
        {"name": "airline", "selector": ".sSHqwe", "type": "text"},
        {
            "name": "departure_time",
            "selector": ".departure",
            "type": "attribute",
            "attribute": "datetime",
        },
        {
            "name": "arrival_time",
            "selector": ".arrival",
            "type": "attribute",
            "attribute": "datetime",
        },
        {"name": "duration", "selector": ".duration", "type": "text"},
        {"name": "stops", "selector": ".stops", "type": "text"},
        {"name": "departure_airport", "selector": ".departure-airport", "type": "text"},
        {"name": "arrival_airport", "selector": ".arrival-airport", "type": "text"},
    ],
}


class FlightParser:
    """Parser de vols Google Flights via JsonCssExtractionStrategy."""

    def __init__(self) -> None:
        self._strategy = JsonCssExtractionStrategy(EXTRACTION_SCHEMA)

    def parse(self, html: str) -> list[GoogleFlightDTO]:
        """Extrait les vols depuis HTML Google Flights."""
        raw_flights = self._strategy.extract(url="", html_content=html)

        if not raw_flights:
            logger.warning(
                "No flight containers found",
                extra={
                    "html_size": len(html),
                    "selector": EXTRACTION_SCHEMA["baseSelector"],
                },
            )
            raise ParsingError(
                "No flights found in HTML", html_size=len(html), flights_found=0
            )

        flights: list[GoogleFlightDTO] = []

        for raw_flight in raw_flights:
            flight = self._parse_flight(raw_flight)
            if flight:
                flights.append(flight)

        if not flights:
            raise ParsingError(
                "Zero valid flights extracted",
                html_size=len(html),
                flights_found=0,
            )

        logger.info(
            "Parsing completed",
            extra={"html_size": len(html), "flights_found": len(flights)},
        )

        return flights

    def _parse_flight(self, raw: dict[str, Any]) -> GoogleFlightDTO | None:
        """Parse un vol depuis les données extraites."""
        try:
            price = self._parse_price(raw.get("price"))
            if price is None:
                logger.warning("Missing price, skipping flight")
                return None

            airline = raw.get("airline")
            if not airline:
                logger.warning("Missing airline, skipping flight")
                return None

            departure_time = self._parse_datetime(raw.get("departure_time"))
            arrival_time = self._parse_datetime(raw.get("arrival_time"))

            if not departure_time or not arrival_time:
                logger.warning("Missing datetime, skipping flight")
                return None

            duration = raw.get("duration") or ""
            stops = self._parse_stops(raw.get("stops"))
            departure_airport = raw.get("departure_airport")
            arrival_airport = raw.get("arrival_airport")

            flight = GoogleFlightDTO(
                price=price,
                airline=airline,
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration=duration,
                stops=stops,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
            )
            return flight

        except ValidationError as e:
            logger.warning("Validation error, skipping flight", extra={"error": str(e)})
            return None
        except Exception as e:
            logger.warning("Parse error, skipping flight", extra={"error": str(e)})
            return None

    def _parse_price(self, price_text: str | None) -> float | None:
        """Extrait le prix depuis le texte."""
        if not price_text:
            return None

        price_clean = re.sub(r"[^\d.,]", "", price_text)
        price_clean = price_clean.replace(",", ".")

        try:
            return float(price_clean)
        except ValueError:
            return None

    def _parse_datetime(self, datetime_str: str | None) -> datetime | None:
        """Parse datetime depuis string ISO."""
        if not datetime_str:
            return None

        try:
            return datetime.fromisoformat(str(datetime_str))
        except ValueError:
            return None

    def _parse_stops(self, stops_text: str | None) -> int | None:
        """Extrait le nombre d'escales."""
        if not stops_text:
            return None

        stops_lower = stops_text.lower()

        if "non-stop" in stops_lower or "nonstop" in stops_lower:
            return 0

        match = re.search(r"(\d+)", stops_text)
        if match:
            return int(match.group(1))

        return None
