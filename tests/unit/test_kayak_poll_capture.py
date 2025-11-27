"""Tests unitaires pour capture_kayak_poll_data."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.utils import capture_kayak_poll_data


@pytest.fixture
def mock_page():
    """Mock Playwright Page."""
    page = AsyncMock()
    page.on = MagicMock()
    return page


@pytest.fixture
def mock_poll_response():
    """Mock Response réseau /poll."""
    response = AsyncMock()
    response.url = "https://www.kayak.fr/s/horizon/api/search/poll?searchId=abc123"
    response.status = 200
    response.text = AsyncMock(return_value='{"results": [{"price": 500}]}')
    return response


@pytest.fixture
def mock_priceprediction_response():
    """Mock Response réseau priceprediction."""
    response = AsyncMock()
    response.url = "https://www.kayak.fr/s/horizon/api/priceprediction?id=xyz"
    response.status = 200
    return response


@pytest.mark.asyncio
async def test_capture_kayak_poll_data_success(
    mock_page, mock_poll_response, mock_priceprediction_response
):
    """Capture poll_data avec succès après priceprediction."""
    call_count = 0

    async def mock_on_response(event_name, handler):
        nonlocal call_count
        if call_count == 0:
            await handler(mock_poll_response)
            call_count += 1
        elif call_count == 1:
            await handler(mock_priceprediction_response)
            call_count += 2

    mock_page.on.side_effect = mock_on_response

    poll_data = await capture_kayak_poll_data(mock_page, timeout=2.0)

    assert poll_data is not None
    assert "results" in poll_data


@pytest.mark.asyncio
async def test_capture_kayak_poll_data_timeout(mock_page):
    """Timeout sans priceprediction retourne None."""
    mock_page.on = MagicMock()

    poll_data = await capture_kayak_poll_data(mock_page, timeout=0.5)

    assert poll_data is None


@pytest.mark.asyncio
async def test_capture_kayak_poll_data_no_poll_responses(
    mock_page, mock_priceprediction_response
):
    """Priceprediction reçu mais aucun poll → retourne None."""

    async def mock_on_response(event_name, handler):
        await handler(mock_priceprediction_response)

    mock_page.on.side_effect = mock_on_response

    poll_data = await capture_kayak_poll_data(mock_page, timeout=2.0)

    assert poll_data is None


@pytest.mark.asyncio
async def test_capture_kayak_poll_data_returns_last_poll(
    mock_page, mock_priceprediction_response
):
    """Retourne dernier poll_data capturé (pas premier)."""
    poll_response_1 = AsyncMock()
    poll_response_1.url = "https://www.kayak.fr/api/search/poll"
    poll_response_1.status = 200
    poll_response_1.text = AsyncMock(return_value='{"results": [{"price": 500}]}')

    poll_response_2 = AsyncMock()
    poll_response_2.url = "https://www.kayak.fr/api/search/poll"
    poll_response_2.status = 200
    poll_response_2.text = AsyncMock(return_value='{"results": [{"price": 450}]}')

    responses = [poll_response_1, poll_response_2, mock_priceprediction_response]
    response_idx = 0

    async def mock_on_response(event_name, handler):
        nonlocal response_idx
        for resp in responses:
            await handler(resp)
            response_idx += 1

    mock_page.on.side_effect = mock_on_response

    poll_data = await capture_kayak_poll_data(mock_page, timeout=2.0)

    assert poll_data is not None
    assert '"price": 450' in poll_data
