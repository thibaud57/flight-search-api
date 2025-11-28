"""Tests unitaires pour app/utils/."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import Cookie

from app.utils import (
    GoogleFlightsUrlError,
    KayakPollCaptureError,
    KayakUrlError,
    build_browser_config_from_fingerprint,
    capture_kayak_poll_data,
    generate_google_flights_url,
    generate_kayak_url,
    get_base_browser_config,
)


class TestBrowserFingerprint:
    """Tests pour browser_fingerprint.py."""

    def test_get_base_browser_config_defaults(self) -> None:
        """Test config par défaut sans params."""
        config = get_base_browser_config()

        assert config.headless is False
        assert config.viewport_width == 1920
        assert config.viewport_height == 1080
        assert config.enable_stealth is False
        assert len(config.extra_args) > 0
        assert "--disable-blink-features=AutomationControlled" in config.extra_args

    def test_get_base_browser_config_with_headers(self) -> None:
        """Test config avec custom headers."""
        custom_headers = {"X-Custom": "test"}
        config = get_base_browser_config(headers=custom_headers)

        assert config.headers == custom_headers

    def test_get_base_browser_config_with_cookies(self) -> None:
        """Test config avec cookies."""
        cookies: list[Cookie] = [
            {
                "name": "test",
                "value": "value",
                "domain": ".google.com",
                "path": "/",
            }
        ]
        config = get_base_browser_config(cookies=cookies)

        assert config.cookies == cookies

    def test_get_base_browser_config_with_proxy(self) -> None:
        """Test config avec proxy."""
        proxy_config = {
            "server": "http://proxy.example.com:8080",
            "username": "user",
            "password": "pass",
        }
        config = get_base_browser_config(proxy_config=proxy_config)

        assert config.proxy_config is not None

    def test_build_browser_config_from_fingerprint(self) -> None:
        """Test config depuis fingerprint capturé."""
        url = "https://www.google.com/travel/flights"
        cookies: list[Cookie] = [
            {
                "name": "SID",
                "value": "test",
                "domain": ".google.com",
                "path": "/",
            }
        ]
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/html"}

        config = build_browser_config_from_fingerprint(
            url=url, cookies=cookies, headers_dict=headers
        )

        assert config.cookies == cookies
        assert "Referer" in config.headers
        assert config.headers["Referer"] == url
        assert "Origin" in config.headers
        assert config.headers["Origin"] == "https://www.google.com"

    def test_build_browser_config_client_hints_preserved(self) -> None:
        """Test que les client hints sont préservés."""
        headers = {
            "sec-ch-ua": '"Chrome";v="142"',
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-site": "same-origin",
            "User-Agent": "Mozilla/5.0",
        }

        config = build_browser_config_from_fingerprint(
            url="https://test.com", cookies=[], headers_dict=headers
        )

        assert "sec-ch-ua" in config.headers
        assert "sec-ch-ua-platform" in config.headers
        assert "sec-fetch-site" in config.headers


class TestGoogleFlightsUrl:
    """Tests pour google_flights_url.py."""

    def test_generate_google_flights_url_valid(self) -> None:
        """Test génération URL avec dates valides."""
        tfs_data = b"flight-data-2025-01-15-2025-01-20"
        tfs_encoded = base64.urlsafe_b64encode(tfs_data).decode().rstrip("=")
        template = f"https://www.google.com/travel/flights?tfs={tfs_encoded}"
        new_dates = ["2025-02-10", "2025-02-15"]

        result = generate_google_flights_url(template, new_dates)

        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(result)
        tfs_result = parse_qs(parsed.query)["tfs"][0]
        tfs_decoded = base64.urlsafe_b64decode(tfs_result + "==").decode()

        assert "2025-02-10" in tfs_decoded
        assert "2025-02-15" in tfs_decoded
        assert "2025-01-15" not in tfs_decoded

    def test_generate_google_flights_url_invalid_date_format(self) -> None:
        """Test avec format date invalide."""
        template = "https://www.google.com/travel/flights?tfs=test"
        invalid_dates = ["2025/01/15", "15-01-2025", "invalid"]

        with pytest.raises(GoogleFlightsUrlError, match="Date invalide"):
            generate_google_flights_url(template, invalid_dates)

    def test_generate_google_flights_url_missing_tfs(self) -> None:
        """Test avec paramètre tfs manquant."""
        template = "https://www.google.com/travel/flights?hl=fr"
        new_dates = ["2025-02-10"]

        with pytest.raises(GoogleFlightsUrlError, match="Paramètre 'tfs' manquant"):
            generate_google_flights_url(template, new_dates)

    def test_generate_google_flights_url_invalid_base64(self) -> None:
        """Test avec tfs non-base64."""
        template = "https://www.google.com/travel/flights?tfs=invalid!!!base64"
        new_dates = ["2025-02-10"]

        with pytest.raises(GoogleFlightsUrlError, match="Erreur décodage base64"):
            generate_google_flights_url(template, new_dates)

    def test_generate_google_flights_url_wrong_dates_count(self) -> None:
        """Test avec nombre de dates incorrect."""
        tfs_data = b"flight-2025-01-15"
        tfs_encoded = base64.urlsafe_b64encode(tfs_data).decode().rstrip("=")
        template = f"https://www.google.com/travel/flights?tfs={tfs_encoded}"
        new_dates = ["2025-02-10", "2025-02-15"]

        with pytest.raises(GoogleFlightsUrlError, match="Nombre de dates incorrect"):
            generate_google_flights_url(template, new_dates)

    def test_generate_google_flights_url_preserves_query_params(self) -> None:
        """Test que les autres params query sont préservés."""
        tfs_data = b"flight-2025-01-15"
        tfs_encoded = base64.urlsafe_b64encode(tfs_data).decode().rstrip("=")
        template = f"https://www.google.com/travel/flights?tfs={tfs_encoded}&hl=fr&curr=EUR"
        new_dates = ["2025-02-10"]

        result = generate_google_flights_url(template, new_dates)

        assert "hl=fr" in result
        assert "curr=EUR" in result


class TestKayakUrl:
    """Tests pour kayak_url.py."""

    def test_generate_kayak_url_valid(self) -> None:
        """Test génération URL Kayak avec dates valides."""
        template = "https://www.kayak.com/flights/PAR-NYC/2025-01-15/2025-01-20"
        new_dates = ["2025-02-10", "2025-02-15"]

        result = generate_kayak_url(template, new_dates)

        assert "2025-02-10" in result
        assert "2025-02-15" in result
        assert "2025-01-15" not in result
        assert "2025-01-20" not in result

    def test_generate_kayak_url_invalid_date_format(self) -> None:
        """Test avec format date invalide."""
        template = "https://www.kayak.com/flights/PAR-NYC/2025-01-15"
        invalid_dates = ["2025/01/15"]

        with pytest.raises(KayakUrlError, match="Date invalide"):
            generate_kayak_url(template, invalid_dates)

    def test_generate_kayak_url_wrong_dates_count(self) -> None:
        """Test avec nombre de dates incorrect."""
        template = "https://www.kayak.com/flights/PAR-NYC/2025-01-15"
        new_dates = ["2025-02-10", "2025-02-15"]

        with pytest.raises(KayakUrlError, match="Nombre de dates incorrect"):
            generate_kayak_url(template, new_dates)

    def test_generate_kayak_url_multi_segment(self) -> None:
        """Test URL multi-segments."""
        template = "https://www.kayak.com/flights/PAR-NYC/2025-01-15/NYC-LON/2025-01-20/LON-PAR/2025-01-25"
        new_dates = ["2025-03-10", "2025-03-15", "2025-03-20"]

        result = generate_kayak_url(template, new_dates)

        assert "2025-03-10" in result
        assert "2025-03-15" in result
        assert "2025-03-20" in result

    def test_generate_kayak_url_preserves_query_params(self) -> None:
        """Test que les params query sont préservés."""
        template = "https://www.kayak.com/flights/PAR-NYC/2025-01-15?sort=price&cabin=e"
        new_dates = ["2025-02-10"]

        result = generate_kayak_url(template, new_dates)

        assert "sort=price" in result
        assert "cabin=e" in result


class TestKayakPollCapture:
    """Tests pour kayak_poll_capture.py."""

    @pytest.mark.asyncio
    async def test_capture_kayak_poll_data_success(self) -> None:
        """Test capture réussie poll_data."""
        page = AsyncMock()

        handler_callback = None

        def mock_on(event_name: str, callback: object) -> None:
            nonlocal handler_callback
            handler_callback = callback

        page.on = mock_on

        async def simulate_responses() -> None:
            await asyncio.sleep(0.1)

            mock_poll_response = MagicMock()
            mock_poll_response.url = "https://www.kayak.com/s/horizon/poll"
            mock_poll_response.status = 200
            mock_poll_response.text = AsyncMock(
                return_value='{"searchId":"test123","results":[]}'
            )

            mock_price_response = MagicMock()
            mock_price_response.url = "https://www.kayak.com/s/horizon/priceprediction"
            mock_price_response.status = 200

            await handler_callback(mock_poll_response)
            await asyncio.sleep(0.1)
            await handler_callback(mock_price_response)

        import asyncio

        task = asyncio.create_task(simulate_responses())
        result = await capture_kayak_poll_data(page, timeout=5.0)
        await task

        assert result is not None
        assert result["searchId"] == "test123"

    @pytest.mark.asyncio
    async def test_capture_kayak_poll_data_timeout(self) -> None:
        """Test timeout si priceprediction jamais reçu."""
        page = AsyncMock()

        async def mock_response_handler(event_name: str, handler: object) -> None:
            pass

        page.on = mock_response_handler

        result = await capture_kayak_poll_data(page, timeout=1.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_capture_kayak_poll_data_invalid_json(self) -> None:
        """Test avec JSON invalide dans poll response."""
        page = AsyncMock()

        async def mock_response_handler(event_name: str, handler: object) -> None:
            if event_name == "response":
                mock_poll_response = MagicMock()
                mock_poll_response.url = "https://www.kayak.com/s/horizon/poll"
                mock_poll_response.status = 200
                mock_poll_response.text = AsyncMock(
                    return_value="invalid json{{{["
                )

                mock_price_response = MagicMock()
                mock_price_response.url = (
                    "https://www.kayak.com/s/horizon/priceprediction"
                )
                mock_price_response.status = 200

                await handler(mock_poll_response)
                await handler(mock_price_response)

        page.on = mock_response_handler

        result = await capture_kayak_poll_data(page, timeout=5.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_capture_kayak_poll_data_no_poll_received(self) -> None:
        """Test quand aucun poll n'est capturé."""
        page = AsyncMock()

        async def mock_response_handler(event_name: str, handler: object) -> None:
            if event_name == "response":
                mock_price_response = MagicMock()
                mock_price_response.url = (
                    "https://www.kayak.com/s/horizon/priceprediction"
                )
                mock_price_response.status = 200

                await handler(mock_price_response)

        page.on = mock_response_handler

        result = await capture_kayak_poll_data(page, timeout=5.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_capture_kayak_poll_data_multiple_polls(self) -> None:
        """Test capture plusieurs poll responses (garde le dernier)."""
        page = AsyncMock()

        handler_callback = None

        def mock_on(event_name: str, callback: object) -> None:
            nonlocal handler_callback
            handler_callback = callback

        page.on = mock_on

        async def simulate_responses() -> None:
            await asyncio.sleep(0.1)

            for i in range(3):
                mock_poll = MagicMock()
                mock_poll.url = "https://www.kayak.com/s/horizon/poll"
                mock_poll.status = 200
                mock_poll.text = AsyncMock(return_value=f'{{"searchId":"poll{i}"}}')
                await handler_callback(mock_poll)
                await asyncio.sleep(0.05)

            mock_price = MagicMock()
            mock_price.url = "https://www.kayak.com/s/horizon/priceprediction"
            mock_price.status = 200
            await handler_callback(mock_price)

        import asyncio

        task = asyncio.create_task(simulate_responses())
        result = await capture_kayak_poll_data(page, timeout=5.0)
        await task

        assert result is not None
        assert result["searchId"] == "poll2"

    @pytest.mark.asyncio
    async def test_capture_kayak_poll_data_exception_handling(self) -> None:
        """Test gestion erreur inattendue."""
        page = AsyncMock()

        def mock_response_handler(event_name: str, handler: object) -> None:
            raise RuntimeError("Unexpected error")

        page.on = mock_response_handler

        with pytest.raises(KayakPollCaptureError, match="Failed to capture poll data"):
            await capture_kayak_poll_data(page, timeout=5.0)
