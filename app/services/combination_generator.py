"""Generateur de combinaisons multi-city (produit cartesien dates par segment)."""

import itertools
import logging
from datetime import date, timedelta

from app.models import DateCombination, DateRange

logger = logging.getLogger(__name__)


class CombinationGenerator:
    """Generateur de combinaisons multi-city (produit cartesien dates par segment)."""

    def generate_combinations(
        self, date_ranges: list[DateRange]
    ) -> list[DateCombination]:
        """Genere produit cartesien dates pour N segments (ordre fixe)."""
        all_dates: list[list[str]] = []
        days_per_segment: list[int] = []

        for date_range in date_ranges:
            start = date.fromisoformat(date_range.start)
            end = date.fromisoformat(date_range.end)
            segment_dates = []
            current = start
            while current <= end:
                segment_dates.append(current.isoformat())
                current += timedelta(days=1)
            all_dates.append(segment_dates)
            days_per_segment.append(len(segment_dates))

        combinations = [
            DateCombination(segment_dates=list(combo))
            for combo in itertools.product(*all_dates)
        ]

        logger.info(
            "Combinations generated",
            extra={
                "segments_count": len(date_ranges),
                "days_per_segment": days_per_segment,
                "total_combinations": len(combinations),
            },
        )

        if combinations:
            logger.debug(
                "Sample combinations",
                extra={
                    "first": combinations[0].segment_dates,
                    "last": combinations[-1].segment_dates,
                },
            )

        return combinations
