# Research: Meeting Summaries Data Ingestion Pipeline

**Date**: 2025-11-30  
**Feature**: 001-meeting-summaries-ingestion

## Overview

This document consolidates research findings and technical decisions for the meeting summaries data ingestion pipeline. All "NEEDS CLARIFICATION" items from the Technical Context have been resolved through research and best practice analysis.

---

## 1. Database Schema Design: PostgreSQL JSONB with Normalized Tables

### Decision
Use a hybrid approach: normalized relational tables for frequently queried fields (workgroup_id, meeting dates, types) combined with JSONB columns for:
- Original JSON preservation (`raw_json` column in each table)
- Nested objects (workingDocs, timestampedVideo)
- Flexible metadata (tags)

### Rationale
- **Performance**: Normalized columns enable efficient filtering and joins (e.g., "find all meetings for workgroup X")
- **Flexibility**: JSONB preserves original data structure and accommodates schema evolution
- **Queryability**: GIN indexes on JSONB enable efficient JSON queries while relational columns support standard SQL operations
- **Provenance**: Storing original JSON ensures full data recovery and auditability

### Alternatives Considered
- **Pure JSONB storage**: Rejected due to poor query performance on normalized fields (workgroup filtering, date ranges)
- **Pure relational storage**: Rejected due to inflexibility for nested structures and schema evolution needs

### Implementation Notes
- Create GIN indexes on all JSONB columns using `jsonb_ops` (default) for broad operator support
- Consider `jsonb_path_ops` for specific columns if containment queries (`@>`) are primary use case
- Use expression indexes on frequently queried JSONB keys if needed: `CREATE INDEX ON table USING GIN ((jsonb_column->'key'))`

---

## 2. Database Access Library: asyncpg vs psycopg2

### Decision
Use **asyncpg** for asynchronous database operations.

### Rationale
- **Performance**: asyncpg demonstrates ~40-60% better performance than psycopg2 in benchmarks (14,100 vs 8,350 ops/sec)
- **Native async support**: Aligns with FastAPI's async-first architecture
- **PostgreSQL binary protocol**: Efficient handling of complex types (arrays, JSONB, UUIDs)
- **Feature set**: Prepared statements, scrollable cursors, custom type support

### Alternatives Considered
- **psycopg2**: Rejected due to synchronous-only nature and lower performance, though it remains a solid choice for synchronous applications
- **SQLAlchemy async**: Considered but adds abstraction layer overhead; asyncpg provides direct PostgreSQL access

### Implementation Notes
- Use `asyncpg` connection pooling for concurrent operations
- Leverage async/await patterns throughout ingestion service
- Use `pytest-asyncio` for async test support

---

## 3. UPSERT Pattern for Idempotent Ingestion

### Decision
Use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` (UPSERT) with last-write-wins strategy.

### Rationale
- **Idempotency**: Allows safe re-running of ingestion without duplicates
- **Atomicity**: Single statement ensures consistency
- **Performance**: Database-level conflict resolution is efficient
- **Simplicity**: No need for separate SELECT-then-INSERT/UPDATE logic

### Implementation Pattern
```sql
INSERT INTO table_name (id, column1, column2, updated_at)
VALUES ($1, $2, $3, NOW())
ON CONFLICT (id) 
DO UPDATE SET
    column1 = EXCLUDED.column1,
    column2 = EXCLUDED.column2,
    updated_at = EXCLUDED.updated_at;
```

### Key Considerations
- Ensure unique constraints/primary keys are properly defined on conflict targets
- Use `EXCLUDED` pseudo-table to reference incoming values
- Consider conditional updates to prevent unnecessary writes (e.g., only update if `updated_at` is older)
- Monitor performance under concurrent loads

### Alternatives Considered
- **SELECT then INSERT/UPDATE**: Rejected due to race conditions and additional round-trips
- **ON CONFLICT DO NOTHING**: Rejected because spec requires last-write-wins updates

---

## 4. CLI Framework: FastAPI vs Click/argparse

### Decision
Use **Click** for CLI interface, with FastAPI components used for shared utilities (dependency injection, async support) if needed.

### Rationale
- **CLI-first**: This is primarily a CLI tool, not a web API
- **Click advantages**: Declarative decorator syntax, better type handling, nested commands support
- **FastAPI context**: While spec mentions FastAPI, the primary interface is CLI; FastAPI can provide shared async utilities if needed
- **Simplicity**: Click is purpose-built for CLI tools and avoids web framework overhead

### Alternatives Considered
- **Pure argparse**: Rejected due to imperative style and less intuitive syntax for complex CLIs
- **FastAPI CLI**: FastAPI is web-first; using it solely for CLI adds unnecessary complexity
- **Typer**: Considered but Click has broader adoption and ecosystem

### Implementation Notes
- Use Click decorators for command definition: `@click.command()`, `@click.option()`
- Leverage Click's type conversion and validation
- Structure commands modularly for testability

---

## 5. JSON Validation: Pydantic Models

### Decision
Use **Pydantic** for JSON structure validation and data modeling.

### Rationale
- **Type safety**: Python type hints with runtime validation
- **Nested structures**: Excellent support for complex nested JSON models
- **Performance**: `model_validate_json()` provides efficient JSON parsing and validation
- **Error messages**: Clear validation errors with field-level details
- **Integration**: Works well with asyncpg and modern Python async patterns

### Implementation Pattern
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class MeetingInfo(BaseModel):
    date: str
    host: Optional[str] = None
    # ... other fields

class MeetingSummary(BaseModel):
    workgroup: str
    workgroup_id: str = Field(..., description="UUID of workgroup")
    meetingInfo: MeetingInfo
    agendaItems: List[AgendaItem] = []
    # ... other fields
```

### Best Practices
- Define separate models for nested structures (MeetingInfo, AgendaItem, etc.)
- Use `Field()` for constraints (min_length, regex patterns, descriptions)
- Validate at each nesting level
- Use `Optional[]` for fields that may be missing
- Leverage `model_validate_json()` for direct JSON string validation

### Alternatives Considered
- **Manual validation**: Rejected due to error-prone and maintenance burden
- **jsonschema**: Considered but Pydantic provides better Python integration and type hints

---

## 6. Containerization and Deployment

### Decision
Use Docker with multi-stage builds, environment variables for secrets, and Supabase-compatible deployment patterns.

### Rationale
- **Portability**: Consistent execution across local and Supabase environments
- **Security**: Environment variables prevent secrets in images
- **Efficiency**: Multi-stage builds minimize image size
- **Stateless**: Container design supports on-demand and scheduled execution

### Docker Best Practices
- Use `python:3.9-slim` or similar lightweight base image
- Multi-stage builds: separate build dependencies from runtime
- Order Dockerfile instructions: place frequently changing layers last
- Use `.dockerignore` to exclude unnecessary files
- Stateless containers: no persistent state in container

### Supabase Deployment Considerations
- Use environment variables for `DATABASE_URL` and credentials
- Ensure container can connect to Supabase PostgreSQL instance
- Support both on-demand execution and scheduled jobs
- Structured logging to stdout/stderr for container-friendly logging

### Alternatives Considered
- **Local-only execution**: Rejected because spec requires Supabase deployment
- **Serverless functions**: Considered but containerized jobs provide more control and consistency

---

## 7. Transaction Boundaries: Per-Meeting Atomicity

### Decision
Process each meeting and all nested entities (agenda items, action items, decision items, discussion points) in a single atomic transaction.

### Rationale
- **Data integrity**: Ensures referential integrity (meeting must exist before agenda items)
- **Consistency**: Either all nested entities are inserted or none (rollback on failure)
- **Error recovery**: Failed meetings don't leave partial data
- **Spec requirement**: Explicitly required in clarifications (FR-024)

### Implementation Pattern
```python
async with connection.transaction():
    # Insert/update meeting
    await upsert_meeting(...)
    # Insert/update all agenda items for this meeting
    for agenda_item in meeting.agendaItems:
        await upsert_agenda_item(...)
        # Insert nested entities
        await upsert_action_items(...)
        await upsert_decision_items(...)
        await upsert_discussion_points(...)
```

### Alternatives Considered
- **Per-record transactions**: Rejected due to referential integrity risks
- **Batch transactions**: Considered but per-meeting provides better error isolation

---

## 8. Workgroup Pre-processing Strategy

### Decision
Extract and create/update all unique workgroups first, before processing any meetings.

### Rationale
- **Referential integrity**: Meetings require workgroups to exist (foreign key constraint)
- **Efficiency**: Single pass through all JSON sources to collect workgroups
- **Spec requirement**: Explicitly required in clarifications (FR-019)

### Implementation Pattern
1. Download and parse all JSON sources
2. Extract all unique workgroups (deduplicate by workgroup_id)
3. UPSERT all workgroups into database
4. Process meetings (which reference existing workgroups)

### Alternatives Considered
- **On-demand workgroup creation**: Rejected due to potential foreign key violations
- **Lazy workgroup creation**: Rejected for same reason

---

## 9. Error Handling and Logging Strategy

### Decision
Use structured JSON logging to stdout/stderr with detailed error context, skip invalid records and continue processing.

### Rationale
- **Container-friendly**: stdout/stderr are standard container logging targets
- **Observability**: Structured JSON enables log aggregation and analysis
- **Resilience**: Skip invalid records rather than failing entire ingestion
- **Debugging**: Detailed error context (record ID, validation errors, field values) aids troubleshooting

### Logging Format
```json
{
  "timestamp": "2025-11-30T12:00:00Z",
  "level": "ERROR",
  "event": "validation_failure",
  "record_id": "uuid-here",
  "source_url": "https://...",
  "errors": ["field 'date' invalid format", "field 'workgroup_id' not a valid UUID"],
  "record_data": {...}
}
```

### Error Handling Strategy
- **Network errors**: Log and continue with next source (if multiple sources)
- **JSON parse errors**: Log and skip source (if single source, fail; if multiple, continue)
- **Validation errors**: Log record details and skip, continue processing
- **Database errors**: Log transaction details, rollback, continue with next record

### Alternatives Considered
- **Fail-fast on any error**: Rejected because spec requires partial success capability
- **Plain text logging**: Rejected because structured logs enable better tooling integration

---

## 10. JSON Structure Compatibility Validation

### Decision
Validate JSON structure compatibility before processing any records from each source.

### Rationale
- **Early failure detection**: Catch schema mismatches before database operations
- **Efficiency**: Avoid partial processing of incompatible data
- **Spec requirement**: Explicitly required (FR-002A, SC-002A)

### Validation Approach
- Check for required top-level fields: `workgroup`, `workgroup_id`, `meetingInfo`, `agendaItems`, `tags`, `type`
- Validate nested structure patterns (meetingInfo.date, agendaItems[].actionItems, etc.)
- Accept optional fields and additional fields (schema flexibility)
- Reject sources with missing required fields

### Implementation
Use Pydantic models with `Optional` fields for flexibility, but require core fields to be present. Validate sample records from each source before full processing.

### Alternatives Considered
- **Validate during processing**: Rejected due to potential partial failures and wasted processing
- **Strict schema matching**: Rejected because spec requires flexibility for additional fields

---

## Summary of Technical Decisions

| Decision Area | Choice | Key Rationale |
|--------------|--------|---------------|
| Schema Design | Hybrid normalized + JSONB | Performance + flexibility |
| DB Library | asyncpg | Performance + async support |
| UPSERT Pattern | INSERT ON CONFLICT DO UPDATE | Idempotency + atomicity |
| CLI Framework | Click | Purpose-built for CLI tools |
| JSON Validation | Pydantic | Type safety + nested support |
| Containerization | Docker multi-stage | Portability + security |
| Transactions | Per-meeting atomic | Data integrity |
| Workgroup Processing | Pre-process all first | Referential integrity |
| Logging | Structured JSON to stdout/stderr | Container-friendly + observability |
| Structure Validation | Pre-process validation | Early failure detection |

---

## Resolved Clarifications

All technical decisions have been made based on:
1. Feature specification requirements
2. Industry best practices
3. Performance considerations
4. Maintainability and simplicity

No outstanding "NEEDS CLARIFICATION" items remain in Technical Context.
