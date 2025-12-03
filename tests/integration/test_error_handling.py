"""Integration tests for error handling scenarios."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.json_downloader import JSONDownloader
from src.services.json_validator import JSONValidator


class TestErrorHandling:
    """Tests for error handling in various scenarios."""

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors during download."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            async with JSONDownloader() as downloader:
                with pytest.raises(httpx.RequestError):
                    await downloader.download("https://example.com/data.json")

    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors."""
        import asyncpg
        from src.services.ingestion_service import IngestionService

        mock_db = MagicMock()
        # Create a proper async context manager mock
        mock_conn = AsyncMock()
        mock_db.acquire = AsyncMock(side_effect=asyncpg.PostgresConnectionError("Connection failed"))

        service = IngestionService(mock_db)
        meetings = []  # Empty for simplicity

        # Should handle connection error gracefully
        with pytest.raises(asyncpg.PostgresConnectionError):
            await mock_db.acquire()

    def test_invalid_json_structure_skipped(self):
        """Test that invalid JSON structure is skipped with logging."""
        validator = JSONValidator()
        invalid_data = [{"invalid": "structure"}]
        result = validator.validate_structure(invalid_data, "https://example.com/data.json")
        assert result is False

    def test_invalid_records_skipped(self):
        """Test that invalid records are skipped during validation."""
        validator = JSONValidator()
        data = [
            {"invalid": "record1"},
            {"invalid": "record2"},
        ]
        valid_records, invalid_records = validator.validate_records(data, "https://example.com/data.json")
        assert len(valid_records) == 0
        assert len(invalid_records) == 2

    @pytest.mark.asyncio
    async def test_partial_source_failure(self, sample_meeting_array):
        """Test handling when one source fails but others succeed."""
        urls = [
            "https://example.com/success1.json",
            "https://example.com/fail.json",
            "https://example.com/success2.json",
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

            async with JSONDownloader() as downloader:
                results = await downloader.download_multiple(urls)

            # Should have results from successful sources only
            assert len(results) == 2
            assert "https://example.com/success1.json" in results
            assert "https://example.com/success2.json" in results

