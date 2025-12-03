# SQL Schema Contract (DDL)

**Date**: 2025-11-30  
**Feature**: 001-meeting-summaries-ingestion

## Overview

This document defines the complete SQL DDL for creating the database schema. All tables use UUID primary keys, foreign key relationships, and include JSONB columns for original data preservation.

---

## Schema Creation Script

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- WORKGROUPS TABLE
-- ============================================================================
CREATE TABLE workgroups (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    raw_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE workgroups IS 'Organizational groups that hold meetings';
COMMENT ON COLUMN workgroups.id IS 'Unique identifier from source workgroup_id';
COMMENT ON COLUMN workgroups.name IS 'Workgroup name from source workgroup field';
COMMENT ON COLUMN workgroups.raw_json IS 'Original JSON data for provenance';

-- Indexes
CREATE INDEX idx_workgroups_raw_json ON workgroups USING GIN (raw_json);

-- ============================================================================
-- MEETINGS TABLE
-- ============================================================================
CREATE TABLE meetings (
    id UUID PRIMARY KEY,
    workgroup_id UUID NOT NULL REFERENCES workgroups(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    type TEXT,
    host TEXT,
    documenter TEXT,
    attendees TEXT[],
    purpose TEXT,
    video_links TEXT[],
    working_docs JSONB,
    timestamped_video JSONB,
    tags JSONB,
    raw_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE meetings IS 'Individual meeting events';
COMMENT ON COLUMN meetings.id IS 'Unique meeting identifier';
COMMENT ON COLUMN meetings.workgroup_id IS 'Reference to parent workgroup';
COMMENT ON COLUMN meetings.date IS 'Meeting date from meetingInfo.date';
COMMENT ON COLUMN meetings.type IS 'Meeting type from source type field';
COMMENT ON COLUMN meetings.host IS 'Meeting host from meetingInfo.host';
COMMENT ON COLUMN meetings.documenter IS 'Person who documented the meeting';
COMMENT ON COLUMN meetings.attendees IS 'Array of attendee names';
COMMENT ON COLUMN meetings.purpose IS 'Meeting purpose/description';
COMMENT ON COLUMN meetings.video_links IS 'Array of video URLs';
COMMENT ON COLUMN meetings.working_docs IS 'Working documents array (JSONB)';
COMMENT ON COLUMN meetings.timestamped_video IS 'Timestamped video segments (JSONB)';
COMMENT ON COLUMN meetings.tags IS 'Tags metadata including topics and emotions (JSONB)';
COMMENT ON COLUMN meetings.raw_json IS 'Original JSON data for provenance';

-- Indexes
CREATE INDEX idx_meetings_workgroup_id ON meetings(workgroup_id);
CREATE INDEX idx_meetings_date ON meetings(date);
CREATE INDEX idx_meetings_type ON meetings(type);
CREATE INDEX idx_meetings_raw_json ON meetings USING GIN (raw_json);
CREATE INDEX idx_meetings_working_docs ON meetings USING GIN (working_docs);
CREATE INDEX idx_meetings_timestamped_video ON meetings USING GIN (timestamped_video);
CREATE INDEX idx_meetings_tags ON meetings USING GIN (tags);

-- ============================================================================
-- AGENDA ITEMS TABLE
-- ============================================================================
CREATE TABLE agenda_items (
    id UUID PRIMARY KEY,
    meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    status TEXT,
    order_index INTEGER,
    raw_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE agenda_items IS 'Topics or items discussed in a meeting';
COMMENT ON COLUMN agenda_items.id IS 'Unique agenda item identifier';
COMMENT ON COLUMN agenda_items.meeting_id IS 'Reference to parent meeting';
COMMENT ON COLUMN agenda_items.status IS 'Agenda item status';
COMMENT ON COLUMN agenda_items.order_index IS 'Order/position of item in agenda';
COMMENT ON COLUMN agenda_items.raw_json IS 'Original JSON data for provenance';

-- Indexes
CREATE INDEX idx_agenda_items_meeting_id ON agenda_items(meeting_id);
CREATE INDEX idx_agenda_items_status ON agenda_items(status);
CREATE INDEX idx_agenda_items_raw_json ON agenda_items USING GIN (raw_json);

-- ============================================================================
-- ACTION ITEMS TABLE
-- ============================================================================
CREATE TABLE action_items (
    id UUID PRIMARY KEY,
    agenda_item_id UUID NOT NULL REFERENCES agenda_items(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    assignee TEXT,
    due_date DATE,
    status TEXT,
    raw_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE action_items IS 'Tasks or actions assigned during a meeting';
COMMENT ON COLUMN action_items.id IS 'Unique action item identifier';
COMMENT ON COLUMN action_items.agenda_item_id IS 'Reference to parent agenda item';
COMMENT ON COLUMN action_items.text IS 'Action item description/text';
COMMENT ON COLUMN action_items.assignee IS 'Person assigned to the action';
COMMENT ON COLUMN action_items.due_date IS 'Due date for the action';
COMMENT ON COLUMN action_items.status IS 'Action item status';
COMMENT ON COLUMN action_items.raw_json IS 'Original JSON data for provenance';

-- Indexes
CREATE INDEX idx_action_items_agenda_item_id ON action_items(agenda_item_id);
CREATE INDEX idx_action_items_assignee ON action_items(assignee);
CREATE INDEX idx_action_items_due_date ON action_items(due_date);
CREATE INDEX idx_action_items_status ON action_items(status);
CREATE INDEX idx_action_items_raw_json ON action_items USING GIN (raw_json);

-- ============================================================================
-- DECISION ITEMS TABLE
-- ============================================================================
CREATE TABLE decision_items (
    id UUID PRIMARY KEY,
    agenda_item_id UUID NOT NULL REFERENCES agenda_items(id) ON DELETE CASCADE,
    decision_text TEXT NOT NULL,
    rationale TEXT,
    effect_scope TEXT,
    raw_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE decision_items IS 'Decisions made during a meeting';
COMMENT ON COLUMN decision_items.id IS 'Unique decision item identifier';
COMMENT ON COLUMN decision_items.agenda_item_id IS 'Reference to parent agenda item';
COMMENT ON COLUMN decision_items.decision_text IS 'Decision description/text';
COMMENT ON COLUMN decision_items.rationale IS 'Rationale for the decision';
COMMENT ON COLUMN decision_items.effect_scope IS 'Scope/impact of the decision';
COMMENT ON COLUMN decision_items.raw_json IS 'Original JSON data for provenance';

-- Indexes
CREATE INDEX idx_decision_items_agenda_item_id ON decision_items(agenda_item_id);
CREATE INDEX idx_decision_items_raw_json ON decision_items USING GIN (raw_json);
-- Optional: Full-text search index on decision_text
-- CREATE INDEX idx_decision_items_decision_text_fts ON decision_items USING GIN (to_tsvector('english', decision_text));

-- ============================================================================
-- DISCUSSION POINTS TABLE
-- ============================================================================
CREATE TABLE discussion_points (
    id UUID PRIMARY KEY,
    agenda_item_id UUID NOT NULL REFERENCES agenda_items(id) ON DELETE CASCADE,
    point_text TEXT NOT NULL,
    raw_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE discussion_points IS 'Discussion points raised during a meeting agenda item';
COMMENT ON COLUMN discussion_points.id IS 'Unique discussion point identifier';
COMMENT ON COLUMN discussion_points.agenda_item_id IS 'Reference to parent agenda item';
COMMENT ON COLUMN discussion_points.point_text IS 'Discussion point text';
COMMENT ON COLUMN discussion_points.raw_json IS 'Original JSON data for provenance';

-- Indexes
CREATE INDEX idx_discussion_points_agenda_item_id ON discussion_points(agenda_item_id);
CREATE INDEX idx_discussion_points_raw_json ON discussion_points USING GIN (raw_json);
-- Optional: Full-text search index on point_text
-- CREATE INDEX idx_discussion_points_point_text_fts ON discussion_points USING GIN (to_tsvector('english', point_text));
```

---

## UPSERT Functions

### Workgroup UPSERT

```sql
-- Function to UPSERT workgroup
CREATE OR REPLACE FUNCTION upsert_workgroup(
    p_id UUID,
    p_name TEXT,
    p_raw_json JSONB
) RETURNS UUID AS $$
BEGIN
    INSERT INTO workgroups (id, name, raw_json, updated_at)
    VALUES (p_id, p_name, p_raw_json, NOW())
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        raw_json = EXCLUDED.raw_json,
        updated_at = NOW();
    RETURN p_id;
END;
$$ LANGUAGE plpgsql;
```

### Meeting UPSERT

```sql
-- Function to UPSERT meeting
CREATE OR REPLACE FUNCTION upsert_meeting(
    p_id UUID,
    p_workgroup_id UUID,
    p_date DATE,
    p_type TEXT,
    p_host TEXT,
    p_documenter TEXT,
    p_attendees TEXT[],
    p_purpose TEXT,
    p_video_links TEXT[],
    p_working_docs JSONB,
    p_timestamped_video JSONB,
    p_tags JSONB,
    p_raw_json JSONB
) RETURNS UUID AS $$
BEGIN
    INSERT INTO meetings (
        id, workgroup_id, date, type, host, documenter,
        attendees, purpose, video_links, working_docs,
        timestamped_video, tags, raw_json, updated_at
    )
    VALUES (
        p_id, p_workgroup_id, p_date, p_type, p_host, p_documenter,
        p_attendees, p_purpose, p_video_links, p_working_docs,
        p_timestamped_video, p_tags, p_raw_json, NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        workgroup_id = EXCLUDED.workgroup_id,
        date = EXCLUDED.date,
        type = EXCLUDED.type,
        host = EXCLUDED.host,
        documenter = EXCLUDED.documenter,
        attendees = EXCLUDED.attendees,
        purpose = EXCLUDED.purpose,
        video_links = EXCLUDED.video_links,
        working_docs = EXCLUDED.working_docs,
        timestamped_video = EXCLUDED.timestamped_video,
        tags = EXCLUDED.tags,
        raw_json = EXCLUDED.raw_json,
        updated_at = NOW();
    RETURN p_id;
END;
$$ LANGUAGE plpgsql;
```

### Agenda Item UPSERT

```sql
-- Function to UPSERT agenda item
CREATE OR REPLACE FUNCTION upsert_agenda_item(
    p_id UUID,
    p_meeting_id UUID,
    p_status TEXT,
    p_order_index INTEGER,
    p_raw_json JSONB
) RETURNS UUID AS $$
BEGIN
    INSERT INTO agenda_items (id, meeting_id, status, order_index, raw_json, updated_at)
    VALUES (p_id, p_meeting_id, p_status, p_order_index, p_raw_json, NOW())
    ON CONFLICT (id) DO UPDATE SET
        meeting_id = EXCLUDED.meeting_id,
        status = EXCLUDED.status,
        order_index = EXCLUDED.order_index,
        raw_json = EXCLUDED.raw_json,
        updated_at = NOW();
    RETURN p_id;
END;
$$ LANGUAGE plpgsql;
```

### Action Item UPSERT

```sql
-- Function to UPSERT action item
CREATE OR REPLACE FUNCTION upsert_action_item(
    p_id UUID,
    p_agenda_item_id UUID,
    p_text TEXT,
    p_assignee TEXT,
    p_due_date DATE,
    p_status TEXT,
    p_raw_json JSONB
) RETURNS UUID AS $$
BEGIN
    INSERT INTO action_items (
        id, agenda_item_id, text, assignee, due_date, status, raw_json, updated_at
    )
    VALUES (
        p_id, p_agenda_item_id, p_text, p_assignee, p_due_date, p_status, p_raw_json, NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        agenda_item_id = EXCLUDED.agenda_item_id,
        text = EXCLUDED.text,
        assignee = EXCLUDED.assignee,
        due_date = EXCLUDED.due_date,
        status = EXCLUDED.status,
        raw_json = EXCLUDED.raw_json,
        updated_at = NOW();
    RETURN p_id;
END;
$$ LANGUAGE plpgsql;
```

### Decision Item UPSERT

```sql
-- Function to UPSERT decision item
CREATE OR REPLACE FUNCTION upsert_decision_item(
    p_id UUID,
    p_agenda_item_id UUID,
    p_decision_text TEXT,
    p_rationale TEXT,
    p_effect_scope TEXT,
    p_raw_json JSONB
) RETURNS UUID AS $$
BEGIN
    INSERT INTO decision_items (
        id, agenda_item_id, decision_text, rationale, effect_scope, raw_json, updated_at
    )
    VALUES (
        p_id, p_agenda_item_id, p_decision_text, p_rationale, p_effect_scope, p_raw_json, NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        agenda_item_id = EXCLUDED.agenda_item_id,
        decision_text = EXCLUDED.decision_text,
        rationale = EXCLUDED.rationale,
        effect_scope = EXCLUDED.effect_scope,
        raw_json = EXCLUDED.raw_json,
        updated_at = NOW();
    RETURN p_id;
END;
$$ LANGUAGE plpgsql;
```

### Discussion Point UPSERT

```sql
-- Function to UPSERT discussion point
CREATE OR REPLACE FUNCTION upsert_discussion_point(
    p_id UUID,
    p_agenda_item_id UUID,
    p_point_text TEXT,
    p_raw_json JSONB
) RETURNS UUID AS $$
BEGIN
    INSERT INTO discussion_points (id, agenda_item_id, point_text, raw_json, updated_at)
    VALUES (p_id, p_agenda_item_id, p_point_text, p_raw_json, NOW())
    ON CONFLICT (id) DO UPDATE SET
        agenda_item_id = EXCLUDED.agenda_item_id,
        point_text = EXCLUDED.point_text,
        raw_json = EXCLUDED.raw_json,
        updated_at = NOW();
    RETURN p_id;
END;
$$ LANGUAGE plpgsql;
```

---

## Schema Validation Queries

### Check Table Existence

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN (
    'workgroups', 'meetings', 'agenda_items', 
    'action_items', 'decision_items', 'discussion_points'
  );
```

### Check Indexes

```sql
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN (
    'workgroups', 'meetings', 'agenda_items',
    'action_items', 'decision_items', 'discussion_points'
  )
ORDER BY tablename, indexname;
```

### Check Foreign Keys

```sql
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public';
```

---

## Migration Notes

- All tables use UUID primary keys (no auto-increment sequences)
- Foreign keys use `ON DELETE CASCADE` for referential integrity
- Timestamps use `TIMESTAMP WITH TIME ZONE` for timezone-aware storage
- JSONB columns use GIN indexes for efficient JSON queries
- Array columns (`attendees`, `video_links`) use PostgreSQL native array types




