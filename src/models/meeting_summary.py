"""Pydantic models for meeting summary validation."""

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MeetingInfo(BaseModel):
    """Meeting information metadata."""

    date: str = Field(..., description="Meeting date in ISO 8601 format")
    host: Optional[str] = Field(None, description="Meeting host name")
    documenter: Optional[str] = Field(None, description="Person who documented the meeting")
    attendees: Optional[List[str]] = Field(
        default_factory=list, description="List of attendee names"
    )
    purpose: Optional[str] = Field(None, description="Meeting purpose/description")
    videoLinks: Optional[List[str]] = Field(default_factory=list, description="List of video URLs")
    workingDocs: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="Working documents array"
    )
    timestampedVideo: Optional[Dict[str, Any]] = Field(
        None, description="Timestamped video segments"
    )

    @field_validator("attendees", "videoLinks")
    @classmethod
    def validate_array_elements(cls, v):
        """Remove empty strings from arrays."""
        if v:
            return [item for item in v if item and str(item).strip()]
        return v or []


class ActionItem(BaseModel):
    """Action item from agenda item."""

    id: Optional[str] = Field(None, description="Action item UUID")
    text: str = Field(..., description="Action item description")
    assignee: Optional[str] = Field(None, description="Person assigned to action")
    dueDate: Optional[str] = Field(None, description="Due date in ISO 8601 format")
    status: Optional[str] = Field(None, description="Action item status")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate action item text is not empty."""
        if not v or not str(v).strip():
            raise ValueError("Action item text cannot be empty")
        return str(v).strip()

    @field_validator("id")
    @classmethod
    def validate_uuid(cls, v):
        """Validate UUID format if provided."""
        if v:
            try:
                uuid.UUID(str(v))
            except ValueError:
                raise ValueError(f"Invalid UUID format: {v}")
        return v


class DecisionItem(BaseModel):
    """Decision item from agenda item."""

    id: Optional[str] = Field(None, description="Decision item UUID")
    decision: str = Field(..., description="Decision text")
    rationale: Optional[str] = Field(None, description="Rationale for decision")
    effectScope: Optional[str] = Field(None, description="Scope/impact of decision")

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, v):
        """Validate decision text is not empty."""
        if not v or not str(v).strip():
            raise ValueError("Decision text cannot be empty")
        return str(v).strip()

    @field_validator("id")
    @classmethod
    def validate_uuid(cls, v):
        """Validate UUID format if provided."""
        if v:
            try:
                uuid.UUID(str(v))
            except ValueError:
                raise ValueError(f"Invalid UUID format: {v}")
        return v


class DiscussionPoint(BaseModel):
    """Discussion point from agenda item."""

    id: Optional[str] = Field(None, description="Discussion point UUID")
    point: str = Field(..., description="Discussion point text")

    @field_validator("point")
    @classmethod
    def validate_point(cls, v):
        """Validate discussion point text is not empty."""
        if not v or not str(v).strip():
            raise ValueError("Discussion point text cannot be empty")
        return str(v).strip()

    @field_validator("id")
    @classmethod
    def validate_uuid(cls, v):
        """Validate UUID format if provided."""
        if v:
            try:
                uuid.UUID(str(v))
            except ValueError:
                raise ValueError(f"Invalid UUID format: {v}")
        return v


class AgendaItem(BaseModel):
    """Agenda item from meeting."""

    id: Optional[str] = Field(None, description="Agenda item UUID")
    status: Optional[str] = Field(None, description="Agenda item status")
    actionItems: Optional[List[ActionItem]] = Field(
        default_factory=list, description="Action items"
    )
    decisionItems: Optional[List[DecisionItem]] = Field(
        default_factory=list, description="Decision items"
    )
    discussionPoints: Optional[List[DiscussionPoint]] = Field(
        default_factory=list, description="Discussion points"
    )

    @field_validator("id")
    @classmethod
    def validate_uuid(cls, v):
        """Validate UUID format if provided."""
        if v:
            try:
                uuid.UUID(str(v))
            except ValueError:
                raise ValueError(f"Invalid UUID format: {v}")
        return v

    @field_validator("actionItems", "decisionItems", "discussionPoints")
    @classmethod
    def validate_nested_collections(cls, v):
        """Ensure empty arrays are preserved as [] not None."""
        return v if v is not None else []


class MeetingSummary(BaseModel):
    """Complete meeting summary record from JSON source."""

    workgroup: str = Field(..., description="Workgroup name")
    workgroup_id: str = Field(..., description="Workgroup UUID")
    meetingInfo: MeetingInfo = Field(..., description="Meeting information")
    agendaItems: List[AgendaItem] = Field(default_factory=list, description="Agenda items")
    tags: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tags metadata")
    type: Optional[str] = Field(None, description="Meeting type")

    # Allow additional fields for schema flexibility
    model_config = ConfigDict(extra="allow")  # Accept additional fields not in model

    @field_validator("workgroup_id")
    @classmethod
    def validate_workgroup_uuid(cls, v):
        """Validate workgroup_id is a valid UUID."""
        try:
            uuid.UUID(str(v))
        except ValueError:
            raise ValueError(f"Invalid workgroup_id UUID format: {v}")
        return v

    @field_validator("workgroup")
    @classmethod
    def validate_workgroup_name(cls, v):
        """Validate workgroup name is not empty."""
        if not v or not str(v).strip():
            raise ValueError("Workgroup name cannot be empty")
        return str(v).strip()

    @field_validator("agendaItems")
    @classmethod
    def validate_agenda_items(cls, v):
        """Ensure empty arrays are preserved as [] not None."""
        return v if v is not None else []


class MeetingSummaryArray(BaseModel):
    """Array of meeting summaries from JSON source."""

    meetings: List[MeetingSummary] = Field(..., description="Array of meeting summaries")

    @classmethod
    def from_json_array(cls, data: List[Dict[str, Any]]) -> "MeetingSummaryArray":
        """Parse array of meeting summary objects."""
        return cls(meetings=[MeetingSummary(**item) for item in data])
