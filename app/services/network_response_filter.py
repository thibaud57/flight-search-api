"""Filtre network events pour identifier API responses Google Flights."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class NetworkResponseFilter:
    """Filtre network events pour identifier API responses Google Flights."""

    def filter_flight_api_responses(
        self, network_events: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Filtre network events pour garder seulement API responses vols."""
        filtered_events: list[dict[str, Any]] = []

        for event in network_events:
            if event.get("event_type") != "response":
                continue

            if event.get("status") != 200:
                continue

            if event.get("resource_type") not in ["xhr", "fetch"]:
                continue

            if "google.com" not in event.get("url", ""):
                continue

            if "response_data" not in event and "body" not in event:
                continue

            filtered_events.append(event)

        input_count = len(network_events)
        output_count = len(filtered_events)

        logger.debug(
            "Network events filtered",
            extra={
                "events_input_count": input_count,
                "events_output_count": output_count,
            },
        )

        if output_count == 0:
            logger.warning(
                "No API responses found after filtering",
                extra={"events_input_count": input_count},
            )

        return filtered_events
