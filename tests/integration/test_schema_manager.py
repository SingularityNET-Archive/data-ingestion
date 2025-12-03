"""Integration tests for schema manager service."""

import pytest
import uuid
from typing import Optional, Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.schema_manager import SchemaManager
from src.models.meeting_summary import MeetingSummary


class TestSchemaManager:
    """Integration tests for SchemaManager."""

    def test_extract_unique_workgroups(self, sample_meeting_summary):
        """Test extraction of unique workgroups from meetings."""
        meeting1 = MeetingSummary(**sample_meeting_summary)
        # Create second meeting with same workgroup
        meeting2_data = sample_meeting_summary.copy()
        meeting2_data["meetingInfo"] = {"date": "2025-01-16"}
        meeting2 = MeetingSummary(**meeting2_data)
        # Create third meeting with different workgroup
        meeting3_data = sample_meeting_summary.copy()
        meeting3_data["workgroup"] = "Different Workgroup"
        meeting3_data["workgroup_id"] = "223e4567-e89b-12d3-a456-426614174000"
        meeting3 = MeetingSummary(**meeting3_data)

        meetings = [meeting1, meeting2, meeting3]
        workgroups = SchemaManager.extract_unique_workgroups(meetings)

        # Should have 2 unique workgroups
        assert len(workgroups) == 2
        assert uuid.UUID(sample_meeting_summary["workgroup_id"]) in workgroups
        assert uuid.UUID("223e4567-e89b-12d3-a456-426614174000") in workgroups

    def test_extract_unique_workgroups_with_original_json(self, sample_meeting_array):
        """Test extraction with original JSON records."""
        meetings = [MeetingSummary(**sample_meeting_array[0])]
        workgroups = SchemaManager.extract_unique_workgroups(
            meetings, original_json_records=sample_meeting_array
        )
        assert len(workgroups) == 1
        workgroup_id = uuid.UUID(sample_meeting_array[0]["workgroup_id"])
        assert workgroup_id in workgroups
        assert "raw_json" in workgroups[workgroup_id]

    @pytest.mark.asyncio
    async def test_upsert_workgroups(self):
        """Test UPSERTing workgroups to database."""
        workgroup_id = uuid.uuid4()
        workgroups = {
            workgroup_id: {
                "id": workgroup_id,
                "name": "Test Workgroup",
                "raw_json": {"workgroup": "Test Workgroup"},
            }
        }

        mock_conn = AsyncMock()
        mock_upsert = AsyncMock()
        with patch("src.models.workgroup.Workgroup.upsert", mock_upsert):
            await SchemaManager.upsert_workgroups(mock_conn, workgroups)

        mock_upsert.assert_called_once()
        call_args = mock_upsert.call_args
        assert call_args[1]["id"] == workgroup_id
        assert call_args[1]["name"] == "Test Workgroup"

    @pytest.mark.asyncio
    async def test_upsert_workgroups_error_handling(self):
        """Test error handling during workgroup UPSERT."""
        workgroup_id = uuid.uuid4()
        workgroups = {
            workgroup_id: {
                "id": workgroup_id,
                "name": "Test Workgroup",
                "raw_json": {},
            }
        }

        mock_conn = AsyncMock()
        mock_upsert = AsyncMock(side_effect=Exception("Database error"))
        with patch("src.models.workgroup.Workgroup.upsert", mock_upsert):
            with pytest.raises(Exception):
                await SchemaManager.upsert_workgroups(mock_conn, workgroups)

