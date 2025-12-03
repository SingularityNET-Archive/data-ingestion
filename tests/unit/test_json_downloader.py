"""Unit tests for JSON downloader service."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.json_downloader import JSONDownloader


@pytest.mark.asyncio
async def test_download_success(mock_httpx_response, sample_meeting_array):
    """Test successful JSON download."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_httpx_response)
        mock_client_class.return_value = mock_client

        async with JSONDownloader() as downloader:
            result = await downloader.download("https://example.com/data.json")

        assert result == sample_meeting_array
        mock_client.get.assert_called_once_with("https://example.com/data.json")


@pytest.mark.asyncio
async def test_download_http_error():
    """Test handling of HTTP errors."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        http_error = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=MagicMock(status_code=404)
        )
        mock_client.get = AsyncMock(side_effect=http_error)
        mock_client_class.return_value = mock_client

        async with JSONDownloader() as downloader:
            with pytest.raises(httpx.HTTPStatusError):
                await downloader.download("https://example.com/notfound.json")


@pytest.mark.asyncio
async def test_download_timeout():
    """Test handling of connection timeout."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        timeout_error = httpx.TimeoutException("Connection timeout")
        mock_client.get = AsyncMock(side_effect=timeout_error)
        mock_client_class.return_value = mock_client

        async with JSONDownloader() as downloader:
            with pytest.raises(httpx.TimeoutException):
                await downloader.download("https://example.com/slow.json")


@pytest.mark.asyncio
async def test_download_invalid_json():
    """Test handling of invalid JSON response."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        response = MagicMock()
        response.status_code = 200
        response.json.side_effect = ValueError("Invalid JSON")
        response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=response)
        mock_client_class.return_value = mock_client

        async with JSONDownloader() as downloader:
            with pytest.raises(ValueError, match="Invalid JSON"):
                await downloader.download("https://example.com/invalid.json")


@pytest.mark.asyncio
async def test_download_non_array_json():
    """Test handling of JSON that is not an array."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"not": "an array"}
        response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=response)
        mock_client_class.return_value = mock_client

        async with JSONDownloader() as downloader:
            with pytest.raises(ValueError, match="Expected JSON array"):
                await downloader.download("https://example.com/object.json")


@pytest.mark.asyncio
async def test_download_request_error():
    """Test handling of request errors."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        request_error = httpx.RequestError("Connection failed")
        mock_client.get = AsyncMock(side_effect=request_error)
        mock_client_class.return_value = mock_client

        async with JSONDownloader() as downloader:
            with pytest.raises(httpx.RequestError):
                await downloader.download("https://example.com/error.json")


@pytest.mark.asyncio
async def test_download_multiple_success(mock_httpx_response, sample_meeting_array):
    """Test downloading from multiple URLs successfully."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_httpx_response)
        mock_client_class.return_value = mock_client

        async with JSONDownloader() as downloader:
            urls = [
                "https://example.com/data1.json",
                "https://example.com/data2.json",
            ]
            result = await downloader.download_multiple(urls)

        assert len(result) == 2
        assert result[urls[0]] == sample_meeting_array
        assert result[urls[1]] == sample_meeting_array


@pytest.mark.asyncio
async def test_download_multiple_partial_failure(mock_httpx_response):
    """Test downloading from multiple URLs with some failures."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        # First call succeeds, second fails
        mock_client.get = AsyncMock(
            side_effect=[
                mock_httpx_response,
                httpx.HTTPStatusError("Not Found", request=MagicMock(), response=MagicMock(status_code=404)),
            ]
        )
        mock_client_class.return_value = mock_client

        async with JSONDownloader() as downloader:
            urls = [
                "https://example.com/data1.json",
                "https://example.com/notfound.json",
            ]
            result = await downloader.download_multiple(urls)

        # Should only have first URL in results
        assert len(result) == 1
        assert "https://example.com/data1.json" in result


@pytest.mark.asyncio
async def test_downloader_timeout_configuration():
    """Test that timeout can be configured."""
    downloader = JSONDownloader(timeout=60)
    assert downloader.timeout == 60


@pytest.mark.asyncio
async def test_downloader_context_manager():
    """Test that downloader works as async context manager."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        async with JSONDownloader() as downloader:
            assert downloader.client is not None

        # Client should be closed after context exit
        mock_client.aclose.assert_called_once()

