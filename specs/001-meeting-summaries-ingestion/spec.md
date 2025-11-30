# Feature Specification: Meeting Summaries Data Ingestion Pipeline

**Feature Branch**: `001-meeting-summaries-ingestion`  
**Created**: 2025-11-30  
**Status**: Draft  
**Input**: User description: "Analyze the meeting-summaries JSON dataset at https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2025/meeting-summaries-array.json, infer its complete structure, and design a fully normalized but JSON-flexible Supabase/PostgreSQL schema. Produce all SQL DDL including table definitions, UUID primary keys, foreign keys, comments, and recommended indexes (including GIN for JSONB). Create tables for workgroups, meetings, agenda items, action items, decision items, and discussion points, storing the original JSON in a raw column for provenance. Then generate a Python FastAPI ingestion script that downloads the JSON, validates its structure, inserts data into the schema, extracts normalized fields, populates relational tables, and stores nested objects in JSONB. Ensure the ingestion code is idempotent, logs conflicts, and gracefully handles missing fields. Finally, output instructions for how to run the ingestion locally and deploy it to Supabase as a containerized job. I want to include historic data from these sources as well. https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2024/meeting-summaries-array.json https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2023/meeting-summaries-array.json https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2022/meeting-summaries-array.json"

## Clarifications

### Session 2025-01-27

- Q: What idempotency conflict resolution strategy should be used when the same record is processed multiple times? → A: UPSERT (INSERT ON CONFLICT DO UPDATE) with last-write-wins - existing records are updated with new data when re-ingesting
- Q: How should the system handle records that fail validation (malformed structure, invalid UUIDs, invalid dates)? → A: Skip invalid records with detailed logging - skip invalid records, log full error details (record ID, validation errors, field values) and continue processing
- Q: What transaction boundaries should be used for data insertion? → A: Per-record transactions - each record processed in its own transaction, commit on success, rollback on failure
- Q: What is the atomicity scope for nested entities (meetings with agenda items, action items, decision items, discussion points)? → A: Per-meeting atomic transactions - each meeting with all nested entities processed atomically as a single unit
- Q: When should workgroups be created relative to meetings? → A: Pre-process all workgroups first - extract all unique workgroups from JSON, create/update them, then process meetings
- Q: What should happen if the same meeting record exists in multiple year files (e.g., a 2024 meeting that was also included in 2023 data)? → A: UPSERT behavior applies - last-write-wins based on ingestion order, with the most recent ingestion taking precedence
- Q: Should the system validate that JSON structure from historic years matches the expected data model before ingestion? → A: Yes - system MUST validate JSON structure compatibility before processing any records
- Q: How should the system handle ingestion of multiple JSON sources - sequential or parallel? → A: Sequential processing by default to maintain transaction integrity and clear error attribution, with option for parallel processing if performance requires it
- Q: What happens if one historic JSON source fails to download or validate while others succeed? → A: System should continue processing remaining sources and log detailed error information for failed sources

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

A data engineer needs to download meeting summary JSON data from multiple remote URLs (2025 current data and historic data from 2022, 2023, 2024), validate its structure compatibility with the data model, and insert it into the database schema with normalized fields extracted and nested objects stored in JSONB columns.

**Why this priority**: Data ingestion is the core functionality that transforms raw JSON into structured database records. This must work correctly for the system to have any value, and must support both current and historic data sources.

**Independent Test**: Can be fully tested by running the ingestion script against a test database with sample JSON data from multiple sources and verifying that all records are inserted correctly with normalized fields populated and original JSON preserved. The ingestion delivers structured, queryable data from unstructured JSON sources across multiple years.

**Acceptance Scenarios**:

1. **Given** multiple valid JSON URLs are provided (2025, 2024, 2023, 2022), **When** the ingestion script runs, **Then** all JSON files are downloaded successfully and parsed without errors
2. **Given** JSON data from multiple sources is downloaded, **When** the ingestion script validates the structure, **Then** JSON structure compatibility with the existing data model is verified before processing any records from each source
3. **Given** valid JSON data is downloaded, **When** the ingestion script processes the data, **Then** all unique workgroups are extracted and created/updated first, then meetings are linked to workgroups, and agenda items with their nested action items, decision items, and discussion points are properly inserted atomically (each meeting and all its nested entities processed in a single transaction)
4. **Given** JSON data contains nested objects (e.g., workingDocs, timestampedVideo), **When** the ingestion script processes records, **Then** these nested objects are stored in JSONB columns while normalized fields are extracted to relational columns
5. **Given** JSON data contains missing or null fields, **When** the ingestion script processes records, **Then** missing fields are handled gracefully without causing errors, and NULL values are inserted where appropriate
6. **Given** JSON data contains invalid records (malformed structure, invalid UUIDs, invalid dates), **When** the ingestion script processes records, **Then** invalid records are skipped, full error details are logged (record ID, validation errors, field values), and processing continues for remaining valid records
7. **Given** one JSON source fails to download or validate while others succeed, **When** the ingestion script processes multiple sources, **Then** processing continues for remaining valid sources, and detailed error information is logged for the failed source
8. **Given** JSON data from multiple sources contains overlapping workgroups or meetings, **When** the ingestion script processes all sources, **Then** all unique workgroups are created/updated first, then all meetings are processed with proper linking, maintaining referential integrity without duplicates

---

### User Story 3 - JSON Structure Compatibility Validation (Priority: P1)

A data engineer needs to verify that JSON data from different years (2022, 2023, 2024, 2025) is compatible with the existing data model before attempting ingestion, preventing data corruption and ensuring consistent schema handling.

**Why this priority**: Structure validation prevents data corruption and ensures all data sources can be processed using the same schema and ingestion logic. This validation must occur before any database operations to avoid partial failures.

**Independent Test**: Can be fully tested by running validation checks against sample JSON from each year and verifying that structure matches expected data model (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type fields). The validation ensures data compatibility and prevents schema mismatches.

**Acceptance Scenarios**:

1. **Given** JSON data from any year (2022, 2023, 2024, 2025), **When** structure validation runs, **Then** the JSON is verified to contain required top-level fields (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type) matching the expected data model
2. **Given** JSON data contains nested structures (meetingInfo, agendaItems), **When** structure validation runs, **Then** nested field structures are verified to match expected patterns (meetingInfo.date, meetingInfo.host, agendaItems[].actionItems, etc.)
3. **Given** JSON data contains optional fields that may be missing or null, **When** structure validation runs, **Then** missing optional fields are accepted without causing validation failure
4. **Given** JSON data contains structural variations or additional fields not in the base model, **When** structure validation runs, **Then** additional fields are accepted (schema is flexible), but core required fields must be present
5. **Given** JSON data fails structure validation, **When** the ingestion script processes multiple sources, **Then** the failed source is skipped with detailed logging, and processing continues for valid sources

---

### User Story 4 - Idempotent Data Processing (Priority: P2)

A data engineer needs to run the ingestion script multiple times without creating duplicate records or losing data integrity, with conflicts logged for review.

**Why this priority**: Idempotency ensures the ingestion process can be safely re-run for updates, error recovery, or data refresh without manual intervention or data corruption.

**Independent Test**: Can be fully tested by running the ingestion script twice with the same data source and verifying that no duplicate records are created, conflicts are logged appropriately, and data integrity is maintained. The idempotent behavior delivers reliable, repeatable data processing.

**Acceptance Scenarios**:

1. **Given** data already exists in the database, **When** the ingestion script runs again with the same source data, **Then** existing records are updated using UPSERT (INSERT ON CONFLICT DO UPDATE) with last-write-wins, preventing duplicate records
2. **Given** a conflict occurs during ingestion (e.g., unique constraint violation), **When** the ingestion script encounters the conflict, **Then** the conflict is logged with details (record identifier, conflict type, timestamp) and processing continues for other records
3. **Given** the same JSON record is processed multiple times, **When** comparing database records, **Then** the most recent version overwrites the existing record (last-write-wins strategy)

---

### User Story 5 - Local Development and Testing (Priority: P2)

A developer needs to run the ingestion pipeline locally for development, testing, and debugging before deploying to production.

**Why this priority**: Local development capability enables rapid iteration, testing, and debugging without affecting production systems or requiring cloud resources.

**Independent Test**: Can be fully tested by following the provided local setup instructions and successfully running the ingestion script against a local database. The local setup delivers a complete development environment for testing and debugging.

**Acceptance Scenarios**:

1. **Given** a developer has a local PostgreSQL database, **When** following the local setup instructions, **Then** the ingestion script can be installed, configured, and executed successfully
2. **Given** the ingestion script is configured for local use, **When** running the script, **Then** it connects to the local database and processes data without errors
3. **Given** local execution completes, **When** querying the local database, **Then** data is correctly inserted and can be verified through standard SQL queries

---

### User Story 6 - Containerized Deployment to Supabase (Priority: P3)

A DevOps engineer needs to deploy the ingestion pipeline as a containerized job that can run on Supabase infrastructure, either on-demand or on a schedule.

**Why this priority**: Containerized deployment enables automated, scalable execution in production environments with proper resource management and isolation.

**Independent Test**: Can be fully tested by building a container image, deploying it to Supabase, and verifying that the ingestion job executes successfully in the containerized environment. The deployment delivers a production-ready, maintainable data ingestion solution.

**Acceptance Scenarios**:

1. **Given** containerization instructions are provided, **When** building the container image, **Then** it includes all necessary dependencies and can be built without errors
2. **Given** a container image is built, **When** deploying to Supabase, **Then** the container runs successfully and connects to the Supabase database
3. **Given** the containerized job is deployed, **When** executing the ingestion, **Then** it processes data correctly and logs execution status and any errors

---

### Edge Cases

- What happens when a JSON URL is unreachable or returns a non-200 status code? → If single source: System should fail with clear error message (network/HTTP errors prevent ingestion). If multiple sources: System should continue processing accessible sources and log detailed error for failed source (partial success is acceptable)
- How does the system handle malformed JSON that cannot be parsed? → If single source: System should fail with clear error message (invalid JSON prevents ingestion). If multiple sources: Failed source is skipped with detailed logging, processing continues for valid sources
- What happens when a required field (e.g., workgroup_id) is missing from a JSON record? → Record is skipped with detailed logging (validation failure logged, processing continues)
- How does the system handle extremely large JSON files or datasets with thousands of records? → System processes files sequentially, handling large datasets within reasonable time limits (e.g., under 10 minutes for all sources combined)
- What happens when database connection fails mid-ingestion? → System should fail with clear error message; previously committed records from successfully processed sources remain in database (per-record transactions ensure partial success is preserved)
- How does the system handle JSON records with circular references or deeply nested structures?
- What happens when UUIDs in the source JSON conflict with existing database records? → UPSERT behavior applies - existing records are updated with new data (last-write-wins)
- How does the system handle special characters, unicode, or emoji in text fields?
- What happens when date fields are in unexpected formats or invalid dates? → Invalid date records are skipped with detailed logging, valid records continue processing
- How does the system handle empty arrays or null values for nested collections (agendaItems, actionItems, etc.)?
- What happens when the same meeting record exists in multiple year files with different data? → Last-write-wins based on ingestion order, with most recent ingestion taking precedence
- How does the system handle JSON sources processed in different orders (e.g., 2022, then 2024, then 2023)? → Order should not affect final data state due to UPSERT behavior, but processing order may affect which version of overlapping records is final
- What happens when JSON sources contain workgroups or meetings that overlap across different years? → UPSERT behavior applies - existing records are updated with new data, maintaining single source of truth per unique identifier

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download JSON data from multiple specified remote URLs (2025, 2024, 2023, 2022)
- **FR-002**: System MUST validate that downloaded data is valid JSON and matches expected structure, verifying JSON structure compatibility with existing data model before processing any records
- **FR-002A**: System MUST verify that JSON contains required top-level fields (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type) matching expected structure
- **FR-002B**: System MUST process multiple JSON sources sequentially by default, maintaining transaction integrity and clear error attribution
- **FR-002C**: System MUST continue processing remaining valid sources if one JSON source fails to download or validate
- **FR-002D**: System MUST log detailed error information for failed JSON sources (source URL, error type, error message, timestamp)
- **FR-003**: System MUST create database tables for workgroups, meetings, agenda_items, action_items, decision_items, and discussion_points
- **FR-004**: System MUST use UUID primary keys for all tables
- **FR-005**: System MUST establish foreign key relationships between tables (meetings → workgroups, agenda_items → meetings, action_items/decision_items/discussion_points → agenda_items)
- **FR-006**: System MUST include a `raw_json` JSONB column in each table to store original JSON data for provenance
- **FR-007**: System MUST create GIN indexes on all JSONB columns for efficient JSON querying
- **FR-008**: System MUST create appropriate indexes on foreign key columns and frequently queried fields
- **FR-009**: System MUST extract normalized fields from JSON and populate relational table columns
- **FR-010**: System MUST store nested objects (e.g., workingDocs, timestampedVideo) in JSONB columns
- **FR-011**: System MUST handle missing or null fields gracefully without failing
- **FR-012**: System MUST implement idempotent insertion logic using UPSERT (INSERT ON CONFLICT DO UPDATE) with last-write-wins strategy to prevent duplicate records and update existing records when re-ingesting, handling overlapping workgroups and meetings across multiple sources without creating duplicates
- **FR-013**: System MUST log conflicts (e.g., unique constraint violations) with details including record identifier, conflict type, timestamp, and source URL
- **FR-014**: System MUST continue processing remaining records even if individual records fail
- **FR-023**: System MUST skip records that fail validation (malformed structure, invalid UUIDs, invalid dates) and log full error details including record identifier, validation errors, and problematic field values
- **FR-024**: System MUST process each meeting record in its own atomic transaction, including all nested entities (agenda items, action items, decision items, discussion points), committing on success and rolling back on failure to ensure data consistency and referential integrity
- **FR-015**: System MUST provide clear instructions for local setup and execution
- **FR-016**: System MUST provide clear instructions for containerized deployment to Supabase
- **FR-017**: System MUST include SQL DDL comments explaining table purposes and column meanings
- **FR-018**: System MUST validate data types (e.g., dates, UUIDs) before insertion
- **FR-019**: System MUST handle workgroup records by pre-processing all unique workgroups from the JSON dataset first (create if not exists, update if exists based on workgroup_id) before processing any meetings
- **FR-020**: System MUST link meetings to workgroups using workgroup_id foreign key (workgroups must exist before meetings are processed)
- **FR-021**: System MUST process agenda items and their nested collections (action items, decision items, discussion points)
- **FR-022**: System MUST preserve original JSON structure in raw_json columns even after normalization
- **FR-025**: System MUST accept additional fields in JSON that are not in the base data model (schema flexibility), while ensuring core required fields are present
- **FR-026**: System MUST process historic data within reasonable time limits (e.g., all sources within 10 minutes for typical dataset sizes)

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

- **SC-001**: System successfully ingests 100% of valid JSON records from all source URLs (2025, 2024, 2023, 2022) without data loss
- **SC-002**: System processes all meeting summary records (approximately 677 total: 122 from 2025, 552 from 2024, 2 from 2023, 1 from 2022) and inserts them into the database within 10 minutes
- **SC-002A**: System validates JSON structure compatibility for 100% of sources before processing any records
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
- **SC-013**: System continues processing remaining valid sources when one source fails, achieving partial success rather than complete failure
- **SC-014**: System applies UPSERT behavior correctly across multiple sources, updating existing records without creating duplicates
- **SC-015**: Historic data ingestion integrates seamlessly with existing 2025 data ingestion, using the same schema and processing logic

## Assumptions

- PostgreSQL/Supabase database is available and accessible
- Python 3.8+ is available for local development
- Docker is available for containerized deployment
- Network access to all GitHub raw content URLs (2025, 2024, 2023, 2022) is available
- Database user has permissions to create tables, indexes, and insert data
- Source JSON structure remains relatively stable across years (schema can accommodate minor variations)
- Historic JSON sources (2022, 2023, 2024) follow the same structure as 2025 data, with potential minor variations in optional fields
- Historic JSON structure is compatible with existing data model (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type fields)
- Workgroup IDs in source JSON are valid UUIDs (or can be validated/skipped if invalid)
- Date fields in source JSON follow consistent formats (ISO 8601 preferred)
- Source JSON does not exceed reasonable size limits (assumed to be processable in memory)
- Historic data may contain overlapping records with existing 2025 data, requiring UPSERT behavior
- Processing order of sources may affect which version of overlapping records is final (last-write-wins)
- Historic JSON sources may have different record counts and file sizes (2024: 552 records, 2023: 2 records, 2022: 1 record)
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
- Integration with other data sources beyond the specified JSON URLs (2025, 2024, 2023, 2022)
- Automated schema migration or evolution
- Data quality scoring or validation rules beyond structure validation
