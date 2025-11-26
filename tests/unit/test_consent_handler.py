"""Tests unitaires pour ConsentHandler."""

from unittest.mock import AsyncMock, patch

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.services.kayak import ConsentHandler


class TestConsentHandler:
    """Tests gestion popup consent Kayak."""

    @pytest.mark.asyncio
    async def test_handle_consent_popup_found(self):
        """Popup présent et cliqué."""
        # Arrange
        mock_page = AsyncMock()
        mock_button = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_button)

        handler = ConsentHandler(consent_selectors=["button[id*='accept']"])

        # Act
        await handler.handle_consent(mock_page)

        # Assert
        mock_page.wait_for_selector.assert_called_once_with(
            "button[id*='accept']", timeout=5000
        )
        mock_button.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_consent_popup_not_found(self):
        """Popup absent (timeout)."""
        # Arrange
        mock_page = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(
            side_effect=PlaywrightTimeoutError("Timeout")
        )

        handler = ConsentHandler(consent_selectors=["button[id*='accept']"])

        # Act (ne doit pas lever d'exception)
        await handler.handle_consent(mock_page)

        # Assert
        mock_page.wait_for_selector.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_consent_multiple_selectors_first_match(self):
        """Plusieurs sélecteurs, premier matche."""
        # Arrange
        mock_page = AsyncMock()
        mock_button = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_button)

        handler = ConsentHandler(
            consent_selectors=["button[id*='accept']", "button[class*='consent']"]
        )

        # Act
        await handler.handle_consent(mock_page)

        # Assert
        mock_page.wait_for_selector.assert_called_once_with(
            "button[id*='accept']", timeout=5000
        )
        mock_button.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_consent_multiple_selectors_second_match(self):
        """Plusieurs sélecteurs, deuxième matche."""
        # Arrange
        mock_page = AsyncMock()
        mock_button = AsyncMock()

        async def wait_for_selector_side_effect(selector: str, timeout: int):
            if selector == "button[id*='accept']":
                raise PlaywrightTimeoutError("Timeout first")
            return mock_button

        mock_page.wait_for_selector = AsyncMock(
            side_effect=wait_for_selector_side_effect
        )

        handler = ConsentHandler(
            consent_selectors=["button[id*='accept']", "button[class*='consent']"]
        )

        # Act
        await handler.handle_consent(mock_page)

        # Assert
        assert mock_page.wait_for_selector.call_count == 2
        mock_button.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_consent_timeout_5s(self):
        """Timeout configuré 5s."""
        # Arrange
        mock_page = AsyncMock()
        mock_button = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_button)

        handler = ConsentHandler(consent_selectors=["button[id*='accept']"])

        # Act
        await handler.handle_consent(mock_page)

        # Assert
        mock_page.wait_for_selector.assert_called_once_with(
            "button[id*='accept']", timeout=5000
        )

    @pytest.mark.asyncio
    async def test_handle_consent_sleep_after_click(self):
        """Sleep 1s après click."""
        # Arrange
        mock_page = AsyncMock()
        mock_button = AsyncMock()
        mock_page.wait_for_selector = AsyncMock(return_value=mock_button)

        handler = ConsentHandler(consent_selectors=["button[id*='accept']"])

        # Act
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await handler.handle_consent(mock_page)

            # Assert
            mock_button.click.assert_called_once()
            mock_sleep.assert_called_once_with(1)
