"""Service de filtrage des vols par segment."""

import logging

from app.models import KayakFlightDTO, SegmentFilters
from app.utils.duration import parse_duration

logger = logging.getLogger(__name__)


class FilterService:
    """Service pour appliquer filtres sur liste de vols."""

    def apply_filters(
        self,
        flights: list[KayakFlightDTO],
        filters: SegmentFilters | None,
        segment_index: int,
    ) -> list[KayakFlightDTO]:
        """Applique filtres sur liste vols et retourne vols filtrés."""
        if filters is None:
            return flights

        if all(
            getattr(filters, field) is None
            for field in [
                "max_duration",
                "max_stops",
                "min_layover_duration",
                "max_layover_duration",
            ]
        ):
            return flights

        flights_before = len(flights)
        filtered_flights = flights

        if filters.max_duration:
            max_duration_minutes = parse_duration(filters.max_duration)
            filtered_flights = [
                f
                for f in filtered_flights
                if self._check_duration(f.duration, max_duration_minutes)
            ]

        if filters.max_stops is not None:
            filtered_flights = [
                f for f in filtered_flights if f.stops <= filters.max_stops
            ]

        if filters.min_layover_duration or filters.max_layover_duration:
            filtered_flights = [
                f
                for f in filtered_flights
                if self._check_layovers(
                    f, filters.min_layover_duration, filters.max_layover_duration
                )
            ]

        flights_after = len(filtered_flights)
        logger.info(
            "Filters applied",
            extra={
                "segment_index": segment_index,
                "filters_applied": filters.model_dump(exclude_none=True),
                "flights_before": flights_before,
                "flights_after": flights_after,
            },
        )

        return filtered_flights

    def _check_duration(self, duration_str: str, max_minutes: int) -> bool:
        """Vérifie si durée vol <= max autorisé."""
        try:
            duration_minutes = parse_duration(duration_str)
            return duration_minutes <= max_minutes
        except ValueError:
            logger.warning(
                "Invalid duration format, skipping flight",
                extra={"duration": duration_str},
            )
            return False

    def _check_layovers(
        self,
        flight: KayakFlightDTO,
        min_duration: str | None,
        max_duration: str | None,
    ) -> bool:
        """Vérifie si TOUTES les layovers respectent les limites (AND logic)."""
        if len(flight.layovers) == 0:
            return True

        try:
            min_minutes = parse_duration(min_duration) if min_duration else None
            max_minutes = parse_duration(max_duration) if max_duration else None

            for layover in flight.layovers:
                layover_minutes = parse_duration(layover.duration)

                if min_minutes is not None and layover_minutes < min_minutes:
                    return False

                if max_minutes is not None and layover_minutes > max_minutes:
                    return False

            return True

        except ValueError as e:
            logger.warning(
                "Invalid layover duration format, skipping flight",
                extra={"error": str(e)},
            )
            return False
