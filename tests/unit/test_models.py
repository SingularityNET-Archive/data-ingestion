"""Unit tests for database models."""

import pytest
import uuid
from src.models.meeting_summary import (
    MeetingSummary,
    MeetingInfo,
    AgendaItem,
    ActionItem,
    DecisionItem,
    DiscussionPoint,
)


class TestMeetingInfo:
    """Tests for MeetingInfo model."""

    def test_valid_meeting_info(self):
        """Test creating valid MeetingInfo."""
        info = MeetingInfo(date="2025-01-15", host="John Doe")
        assert info.date == "2025-01-15"
        assert info.host == "John Doe"

    def test_meeting_info_with_optional_fields(self):
        """Test MeetingInfo with optional fields."""
        info = MeetingInfo(
            date="2025-01-15",
            host="John Doe",
            documenter="Jane Smith",
            attendees=["Alice", "Bob"],
            purpose="Test meeting",
        )
        assert len(info.attendees) == 2

    def test_meeting_info_empty_arrays(self):
        """Test MeetingInfo with empty arrays."""
        info = MeetingInfo(date="2025-01-15", attendees=[], videoLinks=[])
        assert info.attendees == []
        assert info.videoLinks == []

    def test_meeting_info_removes_empty_strings(self):
        """Test that empty strings are removed from arrays."""
        info = MeetingInfo(
            date="2025-01-15",
            attendees=["Alice", "", "Bob", "   "],
            videoLinks=["http://example.com", ""],
        )
        assert "Alice" in info.attendees
        assert "Bob" in info.attendees
        assert "" not in info.attendees
        assert "   " not in info.attendees


class TestActionItem:
    """Tests for ActionItem model."""

    def test_valid_action_item(self):
        """Test creating valid ActionItem."""
        item = ActionItem(text="Complete task", assignee="Alice")
        assert item.text == "Complete task"
        assert item.assignee == "Alice"

    def test_action_item_with_uuid(self):
        """Test ActionItem with valid UUID."""
        item_id = str(uuid.uuid4())
        item = ActionItem(id=item_id, text="Task")
        assert item.id == item_id

    def test_action_item_invalid_uuid(self):
        """Test ActionItem with invalid UUID."""
        with pytest.raises(ValueError, match="Invalid UUID"):
            ActionItem(id="invalid-uuid", text="Task")

    def test_action_item_empty_text(self):
        """Test ActionItem with empty text."""
        with pytest.raises(ValueError, match="cannot be empty"):
            ActionItem(text="")

    def test_action_item_text_trimmed(self):
        """Test that action item text is trimmed."""
        item = ActionItem(text="  Task  ")
        assert item.text == "Task"


class TestDecisionItem:
    """Tests for DecisionItem model."""

    def test_valid_decision_item(self):
        """Test creating valid DecisionItem."""
        item = DecisionItem(decision="Make decision", rationale="Because")
        assert item.decision == "Make decision"
        assert item.rationale == "Because"

    def test_decision_item_empty_text(self):
        """Test DecisionItem with empty decision text."""
        with pytest.raises(ValueError, match="cannot be empty"):
            DecisionItem(decision="")


class TestDiscussionPoint:
    """Tests for DiscussionPoint model."""

    def test_valid_discussion_point(self):
        """Test creating valid DiscussionPoint."""
        point = DiscussionPoint(point="Discussion topic")
        assert point.point == "Discussion topic"

    def test_discussion_point_empty_text(self):
        """Test DiscussionPoint with empty point text."""
        with pytest.raises(ValueError, match="cannot be empty"):
            DiscussionPoint(point="")


class TestAgendaItem:
    """Tests for AgendaItem model."""

    def test_valid_agenda_item(self):
        """Test creating valid AgendaItem."""
        item = AgendaItem(
            id=str(uuid.uuid4()),
            status="completed",
            actionItems=[],
            decisionItems=[],
            discussionPoints=[],
        )
        assert item.status == "completed"
        assert item.actionItems == []

    def test_agenda_item_with_nested_items(self):
        """Test AgendaItem with nested collections."""
        item = AgendaItem(
            id=str(uuid.uuid4()),
            status="pending",
            actionItems=[
                ActionItem(text="Action 1", assignee="Alice"),
                ActionItem(text="Action 2", assignee="Bob"),
            ],
            decisionItems=[DecisionItem(decision="Decision 1")],
            discussionPoints=[DiscussionPoint(point="Point 1")],
        )
        assert len(item.actionItems) == 2
        assert len(item.decisionItems) == 1
        assert len(item.discussionPoints) == 1


class TestMeetingSummary:
    """Tests for MeetingSummary model."""

    def test_valid_meeting_summary(self, sample_meeting_summary):
        """Test creating valid MeetingSummary."""
        summary = MeetingSummary(**sample_meeting_summary)
        assert summary.workgroup == "Test Workgroup"
        assert summary.workgroup_id == "123e4567-e89b-12d3-a456-426614174000"
        assert isinstance(summary.meetingInfo, MeetingInfo)
        assert len(summary.agendaItems) == 1

    def test_meeting_summary_with_nested_data(self, sample_meeting_with_nested_data):
        """Test MeetingSummary with nested collections."""
        summary = MeetingSummary(**sample_meeting_with_nested_data)
        assert len(summary.agendaItems) == 1
        assert len(summary.agendaItems[0].actionItems) == 1
        assert len(summary.agendaItems[0].decisionItems) == 1
        assert len(summary.agendaItems[0].discussionPoints) == 1

    def test_meeting_summary_missing_required_fields(self):
        """Test MeetingSummary with missing required fields."""
        with pytest.raises(Exception):  # Pydantic validation error
            MeetingSummary(workgroup="Test")

    def test_meeting_summary_serialization(self, sample_meeting_summary):
        """Test that MeetingSummary can be serialized."""
        summary = MeetingSummary(**sample_meeting_summary)
        # Should be able to convert to dict
        data = summary.dict()
        assert "workgroup" in data
        assert "meetingInfo" in data

    def test_meeting_summary_json_serialization(self, sample_meeting_summary):
        """Test JSON serialization of MeetingSummary."""
        summary = MeetingSummary(**sample_meeting_summary)
        json_str = summary.json()
        assert isinstance(json_str, str)
        # Should be valid JSON
        import json

        data = json.loads(json_str)
        assert "workgroup" in data

