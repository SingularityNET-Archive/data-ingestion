# Pydantic Validation Schemas

**Date**: 2025-11-30  
**Feature**: 001-meeting-summaries-ingestion

## Overview

This document defines Pydantic models for validating JSON structure compatibility and ensuring data integrity during ingestion. These schemas enforce the expected structure while allowing flexibility for optional fields and additional metadata.

---

## Base Models

### MeetingInfo

Represents meeting metadata from the `meetingInfo` field.

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date

class MeetingInfo(BaseModel):
    """Meeting information metadata."""
    date: str = Field(..., description="Meeting date in ISO 8601 format")
    host: Optional[str] = Field(None, description="Meeting host name")
    documenter: Optional[str] = Field(None, description="Person who documented the meeting")
    attendees: Optional[List[str]] = Field(default_factory=list, description="List of attendee names")
    purpose: Optional[str] = Field(None, description="Meeting purpose/description")
    videoLinks: Optional[List[str]] = Field(default_factory=list, description="List of video URLs")
    workingDocs: Optional[List[dict]] = Field(default_factory=list, description="Working documents array")
    timestampedVideo: Optional[dict] = Field(None, description="Timestamped video segments")
    
    @validator('date')
    def validate_date(cls, v):
        # Validate date format (ISO 8601 preferred)
        # Allow various formats but log warnings for non-standard
        return v
    
    @validator('attendees', 'videoLinks')
    def validate_array_elements(cls, v):
        # Remove empty strings from arrays
        if v:
            return [item for item in v if item and item.strip()]
        return v or []
```

### ActionItem

Represents an action item within an agenda item.

```python
class ActionItem(BaseModel):
    """Action item from agenda item."""
    id: Optional[str] = Field(None, description="Action item UUID")
    text: str = Field(..., description="Action item description")
    assignee: Optional[str] = Field(None, description="Person assigned to action")
    dueDate: Optional[str] = Field(None, description="Due date in ISO 8601 format")
    status: Optional[str] = Field(None, description="Action item status")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Action item text cannot be empty")
        return v.strip()
    
    @validator('id')
    def validate_uuid(cls, v):
        if v:
            # Validate UUID format
            import uuid
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError(f"Invalid UUID format: {v}")
        return v
```

### DecisionItem

Represents a decision made during a meeting.

```python
class DecisionItem(BaseModel):
    """Decision item from agenda item."""
    id: Optional[str] = Field(None, description="Decision item UUID")
    decision: str = Field(..., description="Decision text")
    rationale: Optional[str] = Field(None, description="Rationale for decision")
    effectScope: Optional[str] = Field(None, description="Scope/impact of decision")
    
    @validator('decision')
    def validate_decision(cls, v):
        if not v or not v.strip():
            raise ValueError("Decision text cannot be empty")
        return v.strip()
    
    @validator('id')
    def validate_uuid(cls, v):
        if v:
            import uuid
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError(f"Invalid UUID format: {v}")
        return v
```

### DiscussionPoint

Represents a discussion point within an agenda item.

```python
class DiscussionPoint(BaseModel):
    """Discussion point from agenda item."""
    id: Optional[str] = Field(None, description="Discussion point UUID")
    point: str = Field(..., description="Discussion point text")
    
    @validator('point')
    def validate_point(cls, v):
        if not v or not v.strip():
            raise ValueError("Discussion point text cannot be empty")
        return v.strip()
    
    @validator('id')
    def validate_uuid(cls, v):
        if v:
            import uuid
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError(f"Invalid UUID format: {v}")
        return v
```

### AgendaItem

Represents an agenda item with nested collections.

```python
class AgendaItem(BaseModel):
    """Agenda item from meeting."""
    id: Optional[str] = Field(None, description="Agenda item UUID")
    status: Optional[str] = Field(None, description="Agenda item status")
    actionItems: Optional[List[ActionItem]] = Field(default_factory=list, description="Action items")
    decisionItems: Optional[List[DecisionItem]] = Field(default_factory=list, description="Decision items")
    discussionPoints: Optional[List[DiscussionPoint]] = Field(default_factory=list, description="Discussion points")
    
    @validator('id')
    def validate_uuid(cls, v):
        if v:
            import uuid
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError(f"Invalid UUID format: {v}")
        return v
    
    @validator('actionItems', 'decisionItems', 'discussionPoints')
    def validate_nested_collections(cls, v):
        # Ensure empty arrays are preserved as [] not None
        return v if v is not None else []
```

### MeetingSummary

Top-level model representing a complete meeting summary record.

```python
class MeetingSummary(BaseModel):
    """Complete meeting summary record from JSON source."""
    workgroup: str = Field(..., description="Workgroup name")
    workgroup_id: str = Field(..., description="Workgroup UUID")
    meetingInfo: MeetingInfo = Field(..., description="Meeting information")
    agendaItems: List[AgendaItem] = Field(default_factory=list, description="Agenda items")
    tags: Optional[dict] = Field(default_factory=dict, description="Tags metadata")
    type: Optional[str] = Field(None, description="Meeting type")
    
    # Allow additional fields for schema flexibility
    class Config:
        extra = "allow"  # Accept additional fields not in model
    
    @validator('workgroup_id')
    def validate_workgroup_uuid(cls, v):
        import uuid
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError(f"Invalid workgroup_id UUID format: {v}")
        return v
    
    @validator('workgroup')
    def validate_workgroup_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Workgroup name cannot be empty")
        return v.strip()
    
    @validator('agendaItems')
    def validate_agenda_items(cls, v):
        # Ensure empty arrays are preserved as [] not None
        return v if v is not None else []
```

### MeetingSummaryArray

Wrapper for array of meeting summaries from JSON source.

```python
from typing import List

class MeetingSummaryArray(BaseModel):
    """Array of meeting summaries from JSON source."""
    meetings: List[MeetingSummary] = Field(..., description="Array of meeting summaries")
    
    @classmethod
    def from_json_array(cls, data: List[dict]):
        """Parse array of meeting summary objects."""
        return cls(meetings=[MeetingSummary(**item) for item in data])
    
    @classmethod
    def validate_json_structure(cls, data: List[dict]) -> bool:
        """Validate that JSON array has compatible structure."""
        if not isinstance(data, list):
            return False
        
        # Check at least one record has required fields
        if not data:
            return True  # Empty array is valid
        
        sample = data[0]
        required_fields = ['workgroup', 'workgroup_id', 'meetingInfo', 'agendaItems', 'tags', 'type']
        return all(field in sample for field in required_fields)
```

---

## Validation Functions

### Structure Compatibility Check

```python
def validate_json_structure_compatibility(json_data: List[dict]) -> tuple[bool, List[str]]:
    """
    Validate JSON structure compatibility before processing.
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    if not isinstance(json_data, list):
        return False, ["Root JSON must be an array"]
    
    if not json_data:
        return True, []  # Empty array is valid
    
    # Check required top-level fields in sample record
    sample = json_data[0]
    required_fields = ['workgroup', 'workgroup_id', 'meetingInfo', 'agendaItems', 'tags', 'type']
    
    for field in required_fields:
        if field not in sample:
            errors.append(f"Missing required field: {field}")
    
    # Check nested structure if meetingInfo exists
    if 'meetingInfo' in sample and isinstance(sample['meetingInfo'], dict):
        if 'date' not in sample['meetingInfo']:
            errors.append("Missing required field: meetingInfo.date")
    
    # Check agendaItems is array
    if 'agendaItems' in sample and not isinstance(sample['agendaItems'], list):
        errors.append("agendaItems must be an array")
    
    return len(errors) == 0, errors
```

### Record Validation

```python
def validate_record(record: dict) -> tuple[bool, Optional[MeetingSummary], List[str]]:
    """
    Validate and parse a single meeting summary record.
    
    Returns:
        (is_valid, parsed_model, error_messages)
    """
    errors = []
    
    try:
        model = MeetingSummary(**record)
        return True, model, []
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, None, errors
```

---

## Usage Example

```python
from pydantic import ValidationError
import json

# Load JSON from URL
json_data = download_json(url)

# Validate structure compatibility first
is_compatible, errors = validate_json_structure_compatibility(json_data)
if not is_compatible:
    log_errors(errors)
    raise ValueError("JSON structure incompatible")

# Parse and validate each record
valid_records = []
for record in json_data:
    is_valid, model, record_errors = validate_record(record)
    if is_valid:
        valid_records.append(model)
    else:
        log_validation_errors(record.get('id'), record_errors)
```

---

## Field Mapping to Database

| Pydantic Field | Database Table.Column | Notes |
|----------------|----------------------|-------|
| `workgroup` | `workgroups.name` | Normalized |
| `workgroup_id` | `workgroups.id` | Primary key |
| `meetingInfo.date` | `meetings.date` | Normalized |
| `meetingInfo.host` | `meetings.host` | Normalized |
| `meetingInfo.documenter` | `meetings.documenter` | Normalized |
| `meetingInfo.attendees` | `meetings.attendees` | Array column |
| `meetingInfo.videoLinks` | `meetings.video_links` | Array column |
| `meetingInfo.workingDocs` | `meetings.working_docs` | JSONB |
| `meetingInfo.timestampedVideo` | `meetings.timestamped_video` | JSONB |
| `tags` | `meetings.tags` | JSONB |
| `type` | `meetings.type` | Normalized |
| `agendaItems[].id` | `agenda_items.id` | Primary key |
| `agendaItems[].status` | `agenda_items.status` | Normalized |
| `agendaItems[].actionItems[]` | `action_items.*` | Nested table |
| `agendaItems[].decisionItems[]` | `decision_items.*` | Nested table |
| `agendaItems[].discussionPoints[]` | `discussion_points.*` | Nested table |
| Entire record | `*_tables.raw_json` | JSONB preservation |

---

## Error Handling

### Validation Errors
- **Missing required field**: Log error, skip record, continue processing
- **Invalid UUID format**: Log error with field name, skip record
- **Invalid date format**: Log warning, attempt parsing, skip if fails
- **Empty required text**: Log error, skip record
- **Type mismatch**: Log error with expected vs actual type, skip record

### Logging Format
```json
{
  "timestamp": "2025-11-30T12:00:00Z",
  "level": "ERROR",
  "event": "validation_failure",
  "record_id": "uuid-or-index",
  "source_url": "https://...",
  "field": "workgroup_id",
  "error": "Invalid UUID format: 'not-a-uuid'",
  "value": "not-a-uuid"
}
```








