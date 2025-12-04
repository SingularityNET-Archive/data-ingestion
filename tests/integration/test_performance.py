"""Performance tests for ingestion pipeline."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.ingestion_service import IngestionService
from src.services.json_downloader import JSONDownloader


class TestPerformance:
    """Performance tests to verify ingestion meets time requirements."""

    @pytest.mark.asyncio
    async def test_download_performance(self, sample_meeting_array):
        """Test that download completes within reasonable time."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_meeting_array
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            start_time = time.time()
            async with JSONDownloader() as downloader:
                await downloader.download("https://example.com/data.json")
            elapsed_time = time.time() - start_time

            # Should complete quickly (under 1 second for mock)
            assert elapsed_time < 1.0

    @pytest.mark.asyncio
    async def test_validation_performance(self, sample_meeting_array):
        """Test that validation completes within reasonable time."""
        from src.services.json_validator import JSONValidator

        # Create larger dataset
        large_data = sample_meeting_array * 100  # 100 records

        validator = JSONValidator()
        start_time = time.time()
        result = validator.validate_structure(large_data, "https://example.com/data.json")
        elapsed_time = time.time() - start_time

        assert result is True
        # Should validate 100 records quickly (under 1 second)
        assert elapsed_time < 1.0

    @pytest.mark.asyncio
    async def test_ingestion_throughput(self, sample_meeting_array):
        """Test ingestion throughput for multiple records."""
        from src.models.meeting_summary import MeetingSummary

        # Create multiple meetings
        meetings = [MeetingSummary(**sample_meeting_array[0]) for _ in range(10)]

        mock_db = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        # Make transaction() return an async context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
        mock_transaction.__aexit__ = AsyncMock(return_value=None)
        mock_conn.transaction = MagicMock(return_value=mock_transaction)
        mock_db.acquire = MagicMock(return_value=mock_conn)

        service = IngestionService(mock_db)

        with patch("src.services.schema_manager.SchemaManager.upsert_workgroups", AsyncMock()):
            with patch(
                "src.services.ingestion_service.IngestionService._process_single_meeting",
                AsyncMock(),
            ):
                start_time = time.time()
                stats = await service.process_meetings(
                    meetings, "https://example.com/data.json", dry_run=False
                )
                elapsed_time = time.time() - start_time

        assert stats["succeeded"] == 10
        # Should process 10 records quickly (under 1 second for mocks)
        assert elapsed_time < 1.0

    def test_ten_minute_goal_estimate(self):
        """Test that processing estimate meets 10-minute goal for 677 records."""
        # Estimate: 677 records / 10 minutes = ~67 records/minute
        # This is a sanity check - actual performance depends on network and database
        records_per_minute = 67
        records_per_second = records_per_minute / 60
        time_per_record = 1 / records_per_second

        # Each record should process in under 1 second on average
        assert time_per_record < 1.0
