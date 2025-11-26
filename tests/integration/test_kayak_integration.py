"""Tests intégration Story 10 - KayakUrlBuilder + ConsentHandler."""

from unittest.mock import AsyncMock

import pytest

from app.services.kayak import ConsentHandler
from app.utils import KayakSegment, KayakUrlBuilder


class TestKayakIntegration:
    """Tests intégration composants Story 10."""

    def test_integration_url_builder_with_valid_segments(self):
        """URL builder avec segments valides."""
        # Given
        segments = [
            KayakSegment(origin="PAR", destination="SLZ", date="2026-01-14"),
            KayakSegment(origin="SLZ", destination="LIM", date="2026-03-28"),
            KayakSegment(origin="LIM", destination="PAR", date="2026-04-10"),
        ]
        builder = KayakUrlBuilder()

        # When
        url = builder.build_url(segments)

        # Then
        assert url.startswith("https://www.kayak.fr/flights/")
        assert "PAR-SLZ/2026-01-14" in url
        assert "SLZ-LIM/2026-03-28" in url
        assert "LIM-PAR/2026-04-10" in url
        assert url.endswith("?sort=bestflight_a")

    @pytest.mark.asyncio
    async def test_integration_consent_handler_with_mock_page(self):
        """ConsentHandler avec mock Playwright Page."""
        # Given
        mock_page = AsyncMock()
        mock_button = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_button)

        handler = ConsentHandler(
            consent_selectors=["button[id*='accept']", "button[class*='consent']"]
        )

        # When
        await handler.handle_consent(mock_page)

        # Then
        mock_page.wait_for_selector.assert_called_once()
        mock_button.click.assert_called_once()
