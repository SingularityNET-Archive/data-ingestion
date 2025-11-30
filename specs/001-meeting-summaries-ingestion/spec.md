# Feature Specification: Meeting Summaries Data Ingestion Pipeline

**Feature Branch**: `001-meeting-summaries-ingestion`  
**Created**: 2025-11-30  
**Status**: Draft  
**Input**: User description: "Analyze the meeting-summaries JSON dataset at https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2025/meeting-summaries-array.json, infer its complete structure, and design a fully normalized but JSON-flexible Supabase/PostgreSQL schema. Produce all SQL DDL including table definitions, UUID primary keys, foreign keys, comments, and recommended indexes (including GIN for JSONB). Create tables for workgroups, meetings, agenda items, action items, decision items, and discussion points, storing the original JSON in a raw column for provenance. Then generate a Python FastAPI ingestion script that downloads the JSON, validates its structure, inserts data into the schema, extracts normalized fields, populates relational tables, and stores nested objects in JSONB. Ensure the ingestion code is idempotent, logs conflicts, and gracefully handles missing fields. Finally, output instructions for how to run the ingestion locally and deploy it to Supabase as a containerized job."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Database Schema Creation (Priority: P1)

A data engineer needs to create a normalized database schema that can store meeting summary data from a JSON source while maintaining flexibility for future schema changes and preserving original data for provenance.

**Why this priority**: The database schema is the foundation for all data operations. Without a properly designed schema, data cannot be stored, queried, or analyzed effectively.

**Independent Test**: Can be fully tested by executing SQL DDL statements against a PostgreSQL database and verifying that all tables are created with correct relationships, constraints, and indexes. The schema delivers a structured data model that supports both relational queries and flexible JSON operations.

**Acceptance Scenarios**:

1. **Given** a PostgreSQL database is available, **When** the SQL DDL script is executed, **Then** all required tables (workgroups, meetings, agenda_items, action_items, decision_items, discussion_points) are created with UUID primary keys, foreign key relationships, and appropriate indexes including GIN indexes for JSONB columns
2. **Given** the schema is created, **When** examining table structures, **Then** each table contains a `raw_json` JSONB column for storing original data for provenance
3. **Given** the schema is created, **When** querying table relationships, **Then** foreign key constraints properly link child tables (meetings → workgroups, agenda_items → meetings, action_items/decision_items/discussion_points → agenda_items)

---

### User Story 2 - JSON Data Ingestion (Priority: P1)

A data engineer needs to download meeting summary JSON data from a remote URL, validate its structure, and insert it into the database schema with normalized fields extracted and nested objects stored in JSONB columns.

**Why this priority**: Data ingestion is the core functionality that transforms raw JSON into structured database records. This must work correctly for the system to have any value.

**Independent Test**: Can be fully tested by running the ingestion script against a test database with sample JSON data and verifying that all records are inserted correctly with normalized fields populated and original JSON preserved. The ingestion delivers structured, queryable data from unstructured JSON sources.

**Acceptance Scenarios**:

1. **Given** a valid JSON URL is provided, **When** the ingestion script runs, **Then** the JSON is downloaded successfully and parsed without errors
2. **Given** valid JSON data is downloaded, **When** the ingestion script processes each record, **Then** workgroups are created/updated, meetings are linked to workgroups, and agenda items with their nested action items, decision items, and discussion points are properly inserted
3. **Given** JSON data contains nested objects (e.g., workingDocs, timestampedVideo), **When** the ingestion script processes records, **Then** these nested objects are stored in JSONB columns while normalized fields are extracted to relational columns
4. **Given** JSON data contains missing or null fields, **When** the ingestion script processes records, **Then** missing fields are handled gracefully without causing errors, and NULL values are inserted where appropriate

---

### User Story 3 - Idempotent Data Processing (Priority: P2)

A data engineer needs to run the ingestion script multiple times without creating duplicate records or losing data integrity, with conflicts logged for review.

**Why this priority**: Idempotency ensures the ingestion process can be safely re-run for updates, error recovery, or data refresh without manual intervention or data corruption.

**Independent Test**: Can be fully tested by running the ingestion script twice with the same data source and verifying that no duplicate records are created, conflicts are logged appropriately, and data integrity is maintained. The idempotent behavior delivers reliable, repeatable data processing.

**Acceptance Scenarios**:

1. **Given** data already exists in the database, **When** the ingestion script runs again with the same source data, **Then** duplicate records are not created (using appropriate conflict resolution strategy)
2. **Given** a conflict occurs during ingestion (e.g., unique constraint violation), **When** the ingestion script encounters the conflict, **Then** the conflict is logged with details (record identifier, conflict type, timestamp) and processing continues for other records
3. **Given** the same JSON record is processed multiple times, **When** comparing database records, **Then** the most recent version is preserved or updated appropriately based on the idempotency strategy

---

### User Story 4 - Local Development and Testing (Priority: P2)

A developer needs to run the ingestion pipeline locally for development, testing, and debugging before deploying to production.

**Why this priority**: Local development capability enables rapid iteration, testing, and debugging without affecting production systems or requiring cloud resources.

**Independent Test**: Can be fully tested by following the provided local setup instructions and successfully running the ingestion script against a local database. The local setup delivers a complete development environment for testing and debugging.

**Acceptance Scenarios**:

1. **Given** a developer has a local PostgreSQL database, **When** following the local setup instructions, **Then** the ingestion script can be installed, configured, and executed successfully
2. **Given** the ingestion script is configured for local use, **When** running the script, **Then** it connects to the local database and processes data without errors
3. **Given** local execution completes, **When** querying the local database, **Then** data is correctly inserted and can be verified through standard SQL queries

---

### User Story 5 - Containerized Deployment to Supabase (Priority: P3)

A DevOps engineer needs to deploy the ingestion pipeline as a containerized job that can run on Supabase infrastructure, either on-demand or on a schedule.

**Why this priority**: Containerized deployment enables automated, scalable execution in production environments with proper resource management and isolation.

**Independent Test**: Can be fully tested by building a container image, deploying it to Supabase, and verifying that the ingestion job executes successfully in the containerized environment. The deployment delivers a production-ready, maintainable data ingestion solution.

**Acceptance Scenarios**:

1. **Given** containerization instructions are provided, **When** building the container image, **Then** it includes all necessary dependencies and can be built without errors
2. **Given** a container image is built, **When** deploying to Supabase, **Then** the container runs successfully and connects to the Supabase database
3. **Given** the containerized job is deployed, **When** executing the ingestion, **Then** it processes data correctly and logs execution status and any errors

---

### Edge Cases

- What happens when the JSON URL is unreachable or returns a non-200 status code?
- How does the system handle malformed JSON that cannot be parsed?
- What happens when a required field (e.g., workgroup_id) is missing from a JSON record?
- How does the system handle extremely large JSON files or datasets with thousands of records?
- What happens when database connection fails mid-ingestion?
- How does the system handle JSON records with circular references or deeply nested structures?
- What happens when UUIDs in the source JSON conflict with existing database records?
- How does the system handle special characters, unicode, or emoji in text fields?
- What happens when date fields are in unexpected formats or invalid dates?
- How does the system handle empty arrays or null values for nested collections (agendaItems, actionItems, etc.)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download JSON data from a specified remote URL
- **FR-002**: System MUST validate that downloaded data is valid JSON and matches expected structure
- **FR-003**: System MUST create database tables for workgroups, meetings, agenda_items, action_items, decision_items, and discussion_points
- **FR-004**: System MUST use UUID primary keys for all tables
- **FR-005**: System MUST establish foreign key relationships between tables (meetings → workgroups, agenda_items → meetings, action_items/decision_items/discussion_points → agenda_items)
- **FR-006**: System MUST include a `raw_json` JSONB column in each table to store original JSON data for provenance
- **FR-007**: System MUST create GIN indexes on all JSONB columns for efficient JSON querying
- **FR-008**: System MUST create appropriate indexes on foreign key columns and frequently queried fields
- **FR-009**: System MUST extract normalized fields from JSON and populate relational table columns
- **FR-010**: System MUST store nested objects (e.g., workingDocs, timestampedVideo) in JSONB columns
- **FR-011**: System MUST handle missing or null fields gracefully without failing
- **FR-012**: System MUST implement idempotent insertion logic to prevent duplicate records
- **FR-013**: System MUST log conflicts (e.g., unique constraint violations) with details including record identifier, conflict type, and timestamp
- **FR-014**: System MUST continue processing remaining records even if individual records fail
- **FR-015**: System MUST provide clear instructions for local setup and execution
- **FR-016**: System MUST provide clear instructions for containerized deployment to Supabase
- **FR-017**: System MUST include SQL DDL comments explaining table purposes and column meanings
- **FR-018**: System MUST validate data types (e.g., dates, UUIDs) before insertion
- **FR-019**: System MUST handle workgroup records (create if not exists, update if exists based on workgroup_id)
- **FR-020**: System MUST link meetings to workgroups using workgroup_id foreign key
- **FR-021**: System MUST process agenda items and their nested collections (action items, decision items, discussion points)
- **FR-022**: System MUST preserve original JSON structure in raw_json columns even after normalization

### Key Entities *(include if feature involves data)*

- **Workgroup**: Represents an organizational group that holds meetings. Key attributes: unique identifier (workgroup_id), name. Relationships: one-to-many with meetings.
- **Meeting**: Represents a single meeting event. Key attributes: date, type, host, documenter, attendees, purpose, video links, working documents, timestamped video. Relationships: belongs to one workgroup, has many agenda items.
- **Agenda Item**: Represents a topic or item discussed in a meeting. Key attributes: status. Relationships: belongs to one meeting, has many action items, decision items, and discussion points.
- **Action Item**: Represents a task or action assigned during a meeting. Key attributes: text description, assignee, due date, status. Relationships: belongs to one agenda item.
- **Decision Item**: Represents a decision made during a meeting. Key attributes: decision text, rationale, effect scope. Relationships: belongs to one agenda item.
- **Discussion Point**: Represents a point discussed during a meeting agenda item. Key attributes: point text. Relationships: belongs to one agenda item.
- **Tags**: Metadata associated with meetings including topics covered and emotions. Stored as JSONB in meetings table.
- **Working Documents**: Collection of documents referenced during meetings. Stored as JSONB array in meetings table.
- **Timestamped Video**: Video segments with timestamps. Stored as JSONB in meetings table.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully ingests 100% of valid JSON records from the source URL without data loss
- **SC-002**: System processes all 122 meeting summary records from the source dataset and inserts them into the database within 5 minutes
- **SC-003**: System handles missing or null fields in 100% of records without failing or corrupting data
- **SC-004**: System can be run multiple times (idempotent) without creating duplicate records or data corruption
- **SC-005**: System logs all conflicts with sufficient detail (record ID, conflict type, timestamp) for 100% of conflict cases
- **SC-006**: Database schema supports efficient queries on normalized fields (e.g., find all meetings for a workgroup) with response times under 100ms for typical queries
- **SC-007**: Database schema supports flexible JSON queries on nested objects (e.g., search within workingDocs) using JSONB operators
- **SC-008**: A developer can set up and run the ingestion locally following provided instructions in under 30 minutes
- **SC-009**: A DevOps engineer can build and deploy the containerized job to Supabase following provided instructions in under 1 hour
- **SC-010**: System preserves original JSON data in raw_json columns for 100% of records, enabling full data provenance and recovery
- **SC-011**: System validates JSON structure and rejects invalid data before attempting database insertion, preventing partial data corruption
- **SC-012**: Database schema includes appropriate indexes such that common query patterns (filter by workgroup, filter by date range, search action items) execute efficiently

## Assumptions

- PostgreSQL/Supabase database is available and accessible
- Python 3.8+ is available for local development
- Docker is available for containerized deployment
- Network access to the GitHub raw content URL is available
- Database user has permissions to create tables, indexes, and insert data
- Source JSON structure remains relatively stable (schema can accommodate minor variations)
- Workgroup IDs in source JSON are valid UUIDs
- Date fields in source JSON follow consistent formats (ISO 8601 preferred)
- Source JSON does not exceed reasonable size limits (assumed to be processable in memory)
- Supabase supports containerized job execution (either via Edge Functions, scheduled jobs, or similar infrastructure)

## Dependencies

- PostgreSQL database (local or Supabase)
- Python FastAPI framework and related libraries
- Database connection library (e.g., asyncpg, psycopg2)
- HTTP client library for downloading JSON (e.g., httpx, requests)
- JSON parsing and validation libraries
- Container runtime (Docker) for containerized deployment
- Supabase platform access for deployment target

## Out of Scope

- Real-time data synchronization or streaming ingestion
- Data transformation beyond normalization (e.g., data cleaning, enrichment)
- User interface for viewing or editing ingested data
- API endpoints for querying the ingested data (ingestion only)
- Data export or backup functionality
- Multi-tenant or access control features
- Data versioning or change tracking beyond raw JSON preservation
- Integration with other data sources beyond the specified JSON URL
- Automated schema migration or evolution
- Data quality scoring or validation rules beyond structure validation
