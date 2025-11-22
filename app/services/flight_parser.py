"""Parser de vols Google Flights avec JsonCssExtractionStrategy + aria-label."""

import logging
import re
from datetime import datetime
from typing import Any

from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from pydantic import ValidationError

from app.exceptions import ParsingError
from app.models.google_flight_dto import GoogleFlightDTO

logger = logging.getLogger(__name__)

FLIGHT_SCHEMA: dict[str, Any] = {
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


class FlightParser:
    """Parser de vols Google Flights avec JsonCssExtractionStrategy + aria-label."""

    def __init__(self) -> None:
        """Initialise avec stratégie Crawl4AI."""
        self._strategy = JsonCssExtractionStrategy(FLIGHT_SCHEMA)

    def parse(self, html: str) -> list[GoogleFlightDTO]:
        """Extrait les vols depuis HTML Google Flights."""
        logger.info(
            "🔍 [PARSER] Starting parse",
            extra={"html_size": len(html)},
        )

        raw_results = self._strategy.extract(url="", html_content=html)

        logger.info(
            "📊 [PARSER] CSS extraction completed",
            extra={"raw_results_count": len(raw_results)},
        )

        if not raw_results:
            logger.warning(
                "No flight containers found",
                extra={"html_size": len(html), "selector": "li.pIav2d"},
            )
            raise ParsingError(
                "No flights found in HTML", html_size=len(html), flights_found=0
            )

        flights: list[GoogleFlightDTO] = []

        for idx, raw_flight in enumerate(raw_results):
            logger.debug(
                f"🔎 [PARSER] Processing flight {idx + 1}/{len(raw_results)}",
                extra={"raw_flight_keys": list(raw_flight.keys())},
            )

            aria_label = raw_flight.get("aria_label")
            if not aria_label:
                logger.warning(
                    f"⚠️  [PARSER] Flight {idx + 1}: No aria_label found",
                    extra={"raw_flight": raw_flight},
                )
                continue

            logger.info(
                f"📝 [PARSER] Flight {idx + 1}: aria_label found",
                extra={"aria_label_preview": aria_label[:200]},
            )

            flight = self._parse_aria_label(aria_label)
            if flight:
                logger.info(
                    f"✅ [PARSER] Flight {idx + 1}: Successfully parsed",
                    extra={"price": flight.price, "airline": flight.airline},
                )
                flights.append(flight)
            else:
                logger.warning(
                    f"❌ [PARSER] Flight {idx + 1}: Failed to parse aria_label",
                )

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

    def _parse_aria_label(self, aria_label: str) -> GoogleFlightDTO | None:
        """Parse un vol depuis aria-label."""
        try:
            logger.debug(
                "🔧 [PARSER] Extracting price",
                extra={"aria_label_preview": aria_label[:100]},
            )
            price = self._extract_price(aria_label)
            if price is None:
                logger.warning("❌ [PARSER] Missing price, skipping flight")
                return None
            logger.debug(f"💰 [PARSER] Price extracted: {price}€")

            airline = self._extract_airline(aria_label)
            if not airline:
                logger.warning("❌ [PARSER] Missing airline, skipping flight")
                return None
            logger.debug(f"✈️  [PARSER] Airline extracted: {airline}")

            departure_time = self._extract_departure_time(aria_label)
            arrival_time = self._extract_arrival_time(aria_label)

            if not departure_time or not arrival_time:
                logger.warning(
                    "❌ [PARSER] Missing datetime, skipping flight",
                    extra={
                        "departure_time": str(departure_time),
                        "arrival_time": str(arrival_time),
                    },
                )
                return None
            logger.debug(
                f"🕐 [PARSER] Times extracted: {departure_time} → {arrival_time}"
            )

            duration = self._extract_duration(aria_label)
            stops = self._extract_stops(aria_label)
            logger.debug(f"⏱️  [PARSER] Duration: {duration}, Stops: {stops}")

            flight = GoogleFlightDTO(
                price=price,
                airline=airline,
                departure_time=departure_time,
                arrival_time=arrival_time,
                duration=duration or "",
                stops=stops,
                departure_airport=None,
                arrival_airport=None,
            )
            return flight

        except ValidationError as e:
            logger.debug("Validation error, skipping flight", extra={"error": str(e)})
            return None
        except Exception as e:
            logger.debug("Parse error, skipping flight", extra={"error": str(e)})
            return None

    def _extract_price(self, text: str) -> float | None:
        """Extrait prix depuis 'À partir de 1270 euros'."""
        match = re.search(r"(\d+(?:\s?\d+)*)\s*euros", text)
        if not match:
            return None

        price_str = match.group(1).replace(" ", "")
        try:
            return float(price_str)
        except ValueError:
            return None

    def _extract_airline(self, text: str) -> str | None:
        """Extrait compagnie depuis 'avec ANA' ou 'avec Lufthansa, 1 escale'."""
        match = re.search(r"avec\s+([^.,]+)", text)
        return match.group(1).strip() if match else None

    def _extract_departure_time(self, text: str) -> datetime | None:
        """Extrait départ depuis 'à 18:30 le lundi, décembre 15'."""
        match = re.search(
            r"Départ.*?à\s+(\d{1,2}:\d{2})\s+le\s+[^,]+,\s+(\w+)\s+(\d{1,2})", text
        )
        if not match:
            return None

        time_str = match.group(1)
        month_str = match.group(2).strip()
        day = int(match.group(3))

        month_map = {
            "janvier": 1,
            "février": 2,
            "mars": 3,
            "avril": 4,
            "mai": 5,
            "juin": 6,
            "juillet": 7,
            "août": 8,
            "septembre": 9,
            "octobre": 10,
            "novembre": 11,
            "décembre": 12,
        }

        month = month_map.get(month_str.lower())
        if not month:
            return None

        year = 2025
        hour, minute = map(int, time_str.split(":"))

        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None

    def _extract_arrival_time(self, text: str) -> datetime | None:
        """Extrait arrivée depuis 'arrivée à...à 16:10 le mardi, décembre 16'."""
        match = re.search(
            r"arrivée.*?à\s+(\d{1,2}:\d{2})\s+le\s+[^,]+,\s+(\w+)\s+(\d{1,2})", text
        )
        if not match:
            return None

        time_str = match.group(1)
        month_str = match.group(2).strip()
        day = int(match.group(3))

        month_map = {
            "janvier": 1,
            "février": 2,
            "mars": 3,
            "avril": 4,
            "mai": 5,
            "juin": 6,
            "juillet": 7,
            "août": 8,
            "septembre": 9,
            "octobre": 10,
            "novembre": 11,
            "décembre": 12,
        }

        month = month_map.get(month_str.lower())
        if not month:
            return None

        year = 2025
        hour, minute = map(int, time_str.split(":"))

        try:
            return datetime(year, month, day, hour, minute)
        except ValueError:
            return None

    def _extract_duration(self, text: str) -> str | None:
        """Extrait durée depuis 'Durée totale : 13 h 40 min'."""
        match = re.search(r"Durée totale\s*:\s*(.+?)(?:\.|$)", text)
        return match.group(1).strip() if match else None

    def _extract_stops(self, text: str) -> int | None:
        """Extrait escales depuis 'Vol direct' ou '1 escale'."""
        text_lower = text.lower()

        if "vol direct" in text_lower:
            return 0

        match = re.search(r"(\d+)\s*escale", text_lower)
        return int(match.group(1)) if match else None
