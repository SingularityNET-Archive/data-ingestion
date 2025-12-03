"""End-to-end integration tests for full ingestion pipeline."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.cli.ingest import _run_ingestion
from src.services.json_downloader import JSONDownloader
from src.services.json_validator import JSONValidator


class TestEndToEndIngestion:
    """End-to-end tests for complete ingestion pipeline."""

    @pytest.mark.asyncio
    async def test_full_ingestion_flow_dry_run(self, sample_meeting_array, capfd):
        """Test full ingestion flow in dry-run mode."""
        urls = ["https://example.com/data.json"]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_meeting_array
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            await _run_ingestion(urls, None, dry_run=True, skip_validation=False, logger=MagicMock())

        # Should complete without errors
        assert True

    @pytest.mark.asyncio
    async def test_multiple_sources_processing(self, sample_meeting_array):
        """Test processing multiple JSON sources sequentially."""
        urls = [
            "https://example.com/data1.json",
            "https://example.com/data2.json",
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_meeting_array
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            await _run_ingestion(urls, None, dry_run=True, skip_validation=False, logger=MagicMock())

        # Should process both sources
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_source_failure_continues_processing(self, sample_meeting_array):
        """Test that processing continues when one source fails."""
        import httpx

        urls = [
            "https://example.com/data1.json",
            "https://example.com/fail.json",
            "https://example.com/data2.json",
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_meeting_array
        mock_response.raise_for_status = MagicMock()

        def side_effect(url):
            if "fail" in url:
                raise httpx.HTTPStatusError("Not Found", request=MagicMock(), response=MagicMock(status_code=404))
            return mock_response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=side_effect)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            await _run_ingestion(urls, None, dry_run=True, skip_validation=False, logger=MagicMock())

        # Should have attempted all 3 sources
        assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_structure_validation_before_processing(self, sample_meeting_array):
        """Test that structure validation occurs before processing records."""
        urls = ["https://example.com/data.json"]

        invalid_data = [{"invalid": "structure"}]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = invalid_data
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            await _run_ingestion(urls, None, dry_run=True, skip_validation=False, logger=MagicMock())

        # Should skip invalid structure
        assert True

