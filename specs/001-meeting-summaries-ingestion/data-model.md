# Data Model: Meeting Summaries Ingestion Pipeline

**Date**: 2025-11-30  
**Feature**: 001-meeting-summaries-ingestion

## Overview

This document defines the normalized PostgreSQL/Supabase schema for storing meeting summary data. The schema uses a hybrid approach: normalized relational tables for frequently queried fields combined with JSONB columns for original data preservation and flexible nested structures.

---

## Entity Relationship Diagram

```
workgroups (1) ──< (many) meetings (1) ──< (many) agenda_items (1) ──< (many) action_items
                                                                      └──< (many) decision_items
                                                                      └──< (many) discussion_points
```

---

## Tables

### 1. workgroups

Represents organizational groups that hold meetings.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier (from source `workgroup_id`) |
| `name` | TEXT | NOT NULL | Workgroup name (from source `workgroup`) |
| `raw_json` | JSONB | | Original JSON data for provenance |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record last update timestamp |

**Indexes**:
- Primary key on `id` (automatic)
- GIN index on `raw_json` for JSON queries

**Relationships**:
- One-to-many with `meetings` (meetings.workgroup_id → workgroups.id)

**Validation Rules**:
- `id` must be a valid UUID
- `name` cannot be empty (after trimming whitespace)

---

### 2. meetings

Represents individual meeting events.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique meeting identifier |
| `workgroup_id` | UUID | FOREIGN KEY → workgroups.id, NOT NULL | Reference to parent workgroup |
| `date` | DATE | NOT NULL | Meeting date (from meetingInfo.date) |
| `type` | TEXT | | Meeting type (from source `type`) |
| `host` | TEXT | | Meeting host (from meetingInfo.host) |
| `documenter` | TEXT | | Person who documented the meeting (from meetingInfo.documenter) |
| `attendees` | TEXT[] | | Array of attendee names (from meetingInfo.attendees) |
| `purpose` | TEXT | | Meeting purpose/description |
| `video_links` | TEXT[] | | Array of video URLs (from meetingInfo.videoLinks or similar) |
| `working_docs` | JSONB | | Working documents array (from meetingInfo.workingDocs) |
| `timestamped_video` | JSONB | | Timestamped video segments (from meetingInfo.timestampedVideo) |
| `tags` | JSONB | | Tags metadata including topics and emotions (from source `tags`) |
| `raw_json` | JSONB | NOT NULL | Original JSON data for provenance |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record last update timestamp |

**Indexes**:
- Primary key on `id` (automatic)
- Foreign key index on `workgroup_id` (automatic, but explicit index recommended)
- Index on `date` for date range queries
- Index on `type` for filtering by meeting type
- GIN index on `raw_json` for JSON queries
- GIN index on `working_docs` for JSON queries
- GIN index on `timestamped_video` for JSON queries
- GIN index on `tags` for JSON queries

**Relationships**:
- Many-to-one with `workgroups` (meetings.workgroup_id → workgroups.id)
- One-to-many with `agenda_items` (agenda_items.meeting_id → meetings.id)

**Validation Rules**:
- `id` must be a valid UUID
- `workgroup_id` must reference an existing workgroup
- `date` must be a valid date (ISO 8601 format preferred)
- `attendees` array elements cannot be empty strings
- `video_links` array elements must be valid URLs (if present)

---

### 3. agenda_items

Represents topics or items discussed in a meeting.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique agenda item identifier |
| `meeting_id` | UUID | FOREIGN KEY → meetings.id, NOT NULL | Reference to parent meeting |
| `status` | TEXT | | Agenda item status |
| `order_index` | INTEGER | | Order/position of item in agenda (for preserving order) |
| `raw_json` | JSONB | NOT NULL | Original JSON data for provenance |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record last update timestamp |

**Indexes**:
- Primary key on `id` (automatic)
- Foreign key index on `meeting_id` (automatic, but explicit index recommended)
- Index on `status` for filtering by status
- GIN index on `raw_json` for JSON queries

**Relationships**:
- Many-to-one with `meetings` (agenda_items.meeting_id → meetings.id)
- One-to-many with `action_items` (action_items.agenda_item_id → agenda_items.id)
- One-to-many with `decision_items` (decision_items.agenda_item_id → agenda_items.id)
- One-to-many with `discussion_points` (discussion_points.agenda_item_id → agenda_items.id)

**Validation Rules**:
- `id` must be a valid UUID
- `meeting_id` must reference an existing meeting
- `order_index` should be non-negative (if provided)

---

### 4. action_items

Represents tasks or actions assigned during a meeting.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique action item identifier |
| `agenda_item_id` | UUID | FOREIGN KEY → agenda_items.id, NOT NULL | Reference to parent agenda item |
| `text` | TEXT | NOT NULL | Action item description/text |
| `assignee` | TEXT | | Person assigned to the action |
| `due_date` | DATE | | Due date for the action |
| `status` | TEXT | | Action item status |
| `raw_json` | JSONB | NOT NULL | Original JSON data for provenance |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record last update timestamp |

**Indexes**:
- Primary key on `id` (automatic)
- Foreign key index on `agenda_item_id` (automatic, but explicit index recommended)
- Index on `assignee` for filtering by assignee
- Index on `due_date` for date-based queries
- Index on `status` for filtering by status
- GIN index on `raw_json` for JSON queries

**Relationships**:
- Many-to-one with `agenda_items` (action_items.agenda_item_id → agenda_items.id)

**Validation Rules**:
- `id` must be a valid UUID
- `agenda_item_id` must reference an existing agenda item
- `text` cannot be empty (after trimming whitespace)
- `due_date` must be a valid date (if provided)

---

### 5. decision_items

Represents decisions made during a meeting.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique decision item identifier |
| `agenda_item_id` | UUID | FOREIGN KEY → agenda_items.id, NOT NULL | Reference to parent agenda item |
| `decision_text` | TEXT | NOT NULL | Decision description/text |
| `rationale` | TEXT | | Rationale for the decision |
| `effect_scope` | TEXT | | Scope/impact of the decision |
| `raw_json` | JSONB | NOT NULL | Original JSON data for provenance |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record last update timestamp |

**Indexes**:
- Primary key on `id` (automatic)
- Foreign key index on `agenda_item_id` (automatic, but explicit index recommended)
- Full-text search index on `decision_text` (optional, for text search)
- GIN index on `raw_json` for JSON queries

**Relationships**:
- Many-to-one with `agenda_items` (decision_items.agenda_item_id → agenda_items.id)

**Validation Rules**:
- `id` must be a valid UUID
- `agenda_item_id` must reference an existing agenda item
- `decision_text` cannot be empty (after trimming whitespace)

---

### 6. discussion_points

Represents discussion points raised during a meeting agenda item.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique discussion point identifier |
| `agenda_item_id` | UUID | FOREIGN KEY → agenda_items.id, NOT NULL | Reference to parent agenda item |
| `point_text` | TEXT | NOT NULL | Discussion point text |
| `raw_json` | JSONB | NOT NULL | Original JSON data for provenance |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Record last update timestamp |

**Indexes**:
- Primary key on `id` (automatic)
- Foreign key index on `agenda_item_id` (automatic, but explicit index recommended)
- Full-text search index on `point_text` (optional, for text search)
- GIN index on `raw_json` for JSON queries

**Relationships**:
- Many-to-one with `agenda_items` (discussion_points.agenda_item_id → agenda_items.id)

**Validation Rules**:
- `id` must be a valid UUID
- `agenda_item_id` must reference an existing agenda item
- `point_text` cannot be empty (after trimming whitespace)

---

## Data Types and Constraints

### UUID Primary Keys
- All tables use UUID primary keys for global uniqueness
- UUIDs come from source JSON or are generated during ingestion
- UUID validation occurs before database insertion

### Foreign Key Relationships
- All foreign keys have `ON DELETE CASCADE` to maintain referential integrity
- Foreign key constraints ensure data consistency

### JSONB Columns
- `raw_json`: Stores complete original JSON record for provenance
- `working_docs`: Array of working document objects
- `timestamped_video`: Array/object of timestamped video segments
- `tags`: Object containing topics, emotions, and other metadata

### Array Columns
- `attendees`: TEXT[] - Array of attendee names
- `video_links`: TEXT[] - Array of video URLs

### Timestamps
- `created_at`: Set on first insert, never updated
- `updated_at`: Set on insert and updated on UPSERT

---

## State Transitions

### Meeting Processing Flow
1. **Workgroup Creation**: Extract and UPSERT all unique workgroups first
2. **Meeting Processing**: For each meeting:
   - Validate meeting data
   - UPSERT meeting record
   - Process agenda items atomically (within same transaction)
   - For each agenda item:
     - UPSERT agenda item
     - UPSERT nested action items
     - UPSERT nested decision items
     - UPSERT nested discussion points

### Transaction Boundaries
- Each meeting and all nested entities processed in single atomic transaction
- On failure: entire meeting transaction rolls back
- On success: all nested entities committed together

---

## Data Validation Rules

### Required Fields (from spec FR-002A)
- Top-level: `workgroup`, `workgroup_id`, `meetingInfo`, `agendaItems`, `tags`, `type`
- MeetingInfo: `date` (required)
- AgendaItems: Array (can be empty `[]`)

### Optional Fields
- All other fields are optional and handled gracefully
- Missing fields result in NULL values in database
- Empty arrays stored as `[]` (not NULL) to preserve semantics

### Field Format Validation
- **UUIDs**: Must match UUID format (8-4-4-4-12 hexadecimal)
- **Dates**: ISO 8601 format preferred (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
- **URLs**: Valid URL format for video_links
- **Text**: UTF-8 encoding, supports Unicode and emoji

### Error Handling
- Invalid records skipped with detailed logging
- Validation errors logged with record ID, field name, error message
- Processing continues for remaining valid records

---

## Index Strategy

### Primary Indexes
- UUID primary keys (automatic B-tree indexes)

### Foreign Key Indexes
- Explicit indexes on all foreign key columns for join performance

### Query Optimization Indexes
- `meetings.date`: Date range queries
- `meetings.type`: Filtering by meeting type
- `meetings.workgroup_id`: Joins with workgroups
- `action_items.assignee`: Filtering by assignee
- `action_items.due_date`: Date-based action item queries
- `action_items.status`: Status filtering

### JSONB Indexes (GIN)
- All `raw_json` columns: Full JSON query support
- `meetings.working_docs`: JSON queries on working documents
- `meetings.timestamped_video`: JSON queries on video segments
- `meetings.tags`: JSON queries on tags/metadata

### Full-Text Search (Optional)
- `decision_items.decision_text`: Text search on decisions
- `discussion_points.point_text`: Text search on discussion points

---

## Data Normalization

### Normalized Fields
- Workgroup name extracted to `workgroups.name`
- Meeting date, type, host, documenter extracted to relational columns
- Action item text, assignee, due date, status extracted to relational columns
- Decision text, rationale, effect scope extracted to relational columns
- Discussion point text extracted to relational column

### JSONB Preservation
- Complete original JSON preserved in `raw_json` columns
- Nested objects (workingDocs, timestampedVideo) stored in JSONB
- Tags metadata stored in JSONB
- Enables full data recovery and schema evolution

---

## Idempotency Strategy

### UPSERT Pattern
All tables use `INSERT ... ON CONFLICT DO UPDATE`:
- **Conflict Target**: Primary key (`id`)
- **Update Strategy**: Last-write-wins (update all fields with new values)
- **Timestamp Handling**: `updated_at` set to current timestamp on conflict

### Conflict Resolution
- Duplicate workgroups: Update name if changed
- Duplicate meetings: Update all fields with latest data
- Duplicate nested entities: Update with latest data
- Conflicts logged with details (record ID, conflict type, timestamp)

---

## Data Provenance

### Original JSON Preservation
- Every table includes `raw_json` JSONB column
- Stores complete original JSON record from source
- Enables:
  - Full data recovery
  - Schema evolution support
  - Audit trail
  - Debugging and troubleshooting

### Source Tracking
- Source URL tracked in logs (not in database schema)
- Ingestion timestamp tracked via `created_at` and `updated_at`
- Multiple source handling: Last-write-wins based on ingestion order

---

## Schema Evolution Considerations

### Flexible Schema Design
- JSONB columns accommodate schema changes without migrations
- Additional fields in source JSON stored in `raw_json`
- Normalized columns can be added via migrations if needed
- Backward compatibility: Old records preserve original structure

### Migration Strategy
- Schema changes require DDL migrations
- New normalized columns can be added with default values
- Existing data preserved in `raw_json` for reference










