"""Integration tests for ingestion service."""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.ingestion_service import IngestionService
from src.models.meeting_summary import MeetingSummary


class TestIngestionService:
    """Integration tests for IngestionService."""

    @pytest.fixture
    def mock_db_connection(self):
        """Fixture providing mock database connection."""
        mock_conn = AsyncMock()
        # Make mock_conn work as async context manager
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        
        mock_db = MagicMock()
        # Make acquire() return mock_conn directly (not awaited) so it can be used as async context manager
        mock_db.acquire = MagicMock(return_value=mock_conn)
        mock_db.create_pool = AsyncMock()
        mock_db.close_pool = AsyncMock()
        return mock_db

    @pytest.mark.asyncio
    async def test_process_meetings_dry_run(self, mock_db_connection, sample_meeting_array):
        """Test processing meetings in dry-run mode."""
        service = IngestionService(mock_db_connection)
        meetings = [MeetingSummary(**sample_meeting_array[0])]

        stats = await service.process_meetings(
            meetings, "https://example.com/data.json", dry_run=True
        )

        assert stats["processed"] == 1
        assert stats["succeeded"] == 1
        assert stats["failed"] == 0
        # Should not call database in dry-run
        mock_db_connection.acquire.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_meetings_workgroup_extraction(self, mock_db_connection, sample_meeting_array):
        """Test that workgroups are extracted and processed first."""
        service = IngestionService(mock_db_connection)
        meetings = [MeetingSummary(**sample_meeting_array[0])]

        # Get the mock_conn from the fixture (it's already set up as async context manager)
        mock_conn = mock_db_connection.acquire.return_value
        mock_transaction = AsyncMock()
        mock_conn.transaction = AsyncMock(return_value=mock_transaction)

        with patch("src.services.schema_manager.SchemaManager.upsert_workgroups", AsyncMock()):
            with patch("src.services.ingestion_service.IngestionService._process_single_meeting", AsyncMock()):
                stats = await service.process_meetings(
                    meetings, "https://example.com/data.json", dry_run=False
                )

        assert stats["workgroups_created"] == 1

    @pytest.mark.asyncio
    async def test_process_meetings_atomic_transaction(self, mock_db_connection, sample_meeting_array):
        """Test that each meeting is processed in atomic transaction."""
        service = IngestionService(mock_db_connection)
        meetings = [MeetingSummary(**sample_meeting_array[0])]

        # Get the mock_conn from the fixture
        mock_conn = mock_db_connection.acquire.return_value
        mock_transaction = AsyncMock()
        mock_conn.transaction = AsyncMock(return_value=mock_transaction)

        with patch("src.services.schema_manager.SchemaManager.upsert_workgroups", AsyncMock()):
            with patch("src.services.ingestion_service.IngestionService._process_single_meeting", AsyncMock()):
                await service.process_meetings(
                    meetings, "https://example.com/data.json", dry_run=False
                )

        # Should have called transaction for meeting processing
        assert mock_conn.transaction.called

    @pytest.mark.asyncio
    async def test_process_meetings_error_handling(self, mock_db_connection, sample_meeting_array):
        """Test error handling during meeting processing."""
        service = IngestionService(mock_db_connection)
        meetings = [MeetingSummary(**sample_meeting_array[0])]

        # Get the mock_conn from the fixture
        mock_conn = mock_db_connection.acquire.return_value
        mock_transaction = AsyncMock()
        mock_conn.transaction = AsyncMock(return_value=mock_transaction)

        with patch("src.services.schema_manager.SchemaManager.upsert_workgroups", AsyncMock()):
            with patch(
                "src.services.ingestion_service.IngestionService._process_single_meeting",
                AsyncMock(side_effect=Exception("Processing error")),
            ):
                stats = await service.process_meetings(
                    meetings, "https://example.com/data.json", dry_run=False
                )

        assert stats["failed"] == 1
        assert stats["succeeded"] == 0

    @pytest.mark.asyncio
    async def test_process_empty_meetings_list(self, mock_db_connection):
        """Test processing empty meetings list."""
        service = IngestionService(mock_db_connection)
        stats = await service.process_meetings([], "https://example.com/data.json")
        assert stats["processed"] == 0
        assert stats["succeeded"] == 0

