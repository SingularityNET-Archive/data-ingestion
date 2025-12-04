# Feature Specification: Include Historic Meeting Summaries Data

**Feature Branch**: `002-include-historic-data`  
**Created**: 2025-11-30  
**Status**: Draft  
**Input**: User description: "I want to include historic data from these sources as well. https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2024/meeting-summaries-array.json https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2023/meeting-summaries-array.json https://raw.githubusercontent.com/SingularityNET-Archive/SingularityNET-Archive/refs/heads/main/Data/Snet-Ambassador-Program/Meeting-Summaries/2022/meeting-summaries-array.json"

## Clarifications

### Session 2025-01-27

- Q: What should happen if the same meeting record exists in multiple year files (e.g., a 2024 meeting that was also included in 2023 data)? → A: UPSERT behavior applies - last-write-wins based on ingestion order, with the most recent ingestion taking precedence
- Q: Should the system validate that JSON structure from historic years matches the expected data model before ingestion? → A: Yes - system MUST validate JSON structure compatibility before processing any records
- Q: How should the system handle ingestion of multiple JSON sources - sequential or parallel? → A: Sequential processing by default to maintain transaction integrity and clear error attribution, with option for parallel processing if performance requires it
- Q: What happens if one historic JSON source fails to download or validate while others succeed? → A: System should continue processing remaining sources and log detailed error information for failed sources

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Historic Data Ingestion (Priority: P1)

A data engineer needs to ingest historic meeting summary data from multiple JSON sources (2022, 2023, 2024) into the existing database schema, ensuring all records are processed correctly and data model compatibility is validated before insertion.

**Why this priority**: Historic data ingestion is the core functionality that extends the system's data coverage to include past years. This must work correctly to provide complete historical context for meeting summaries analysis.

**Independent Test**: Can be fully tested by running the ingestion script against multiple historic JSON URLs and verifying that all records from all sources are inserted correctly, JSON structure is validated for compatibility, and existing records are updated appropriately without duplicates. The ingestion delivers comprehensive historical data coverage from multiple sources.

**Acceptance Scenarios**:

1. **Given** multiple historic JSON URLs (2022, 2023, 2024) are provided, **When** the ingestion script runs, **Then** all JSON files are downloaded successfully and parsed without errors
2. **Given** historic JSON data is downloaded, **When** the ingestion script validates the structure, **Then** JSON structure compatibility with the existing data model is verified before processing any records
3. **Given** historic JSON data contains records with the same identifiers as existing database records, **When** the ingestion script processes the data, **Then** existing records are updated (UPSERT) with last-write-wins behavior, and no duplicate records are created
4. **Given** historic JSON data from multiple sources contains overlapping workgroups or meetings, **When** the ingestion script processes all sources, **Then** all unique workgroups are created/updated first, then all meetings are processed with proper linking, maintaining referential integrity
5. **Given** one historic JSON source fails to download or validate, **When** the ingestion script processes multiple sources, **Then** processing continues for remaining valid sources, and detailed error information is logged for the failed source

---

### User Story 2 - JSON Structure Compatibility Validation (Priority: P1)

A data engineer needs to verify that historic JSON data from different years (2022, 2023, 2024) is compatible with the existing data model before attempting ingestion, preventing data corruption and ensuring consistent schema handling.

**Why this priority**: Structure validation prevents data corruption and ensures all historic data can be processed using the same schema and ingestion logic. This validation must occur before any database operations to avoid partial failures.

**Independent Test**: Can be fully tested by running validation checks against sample JSON from each historic year and verifying that structure matches expected data model (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type fields). The validation ensures data compatibility and prevents schema mismatches.

**Acceptance Scenarios**:

1. **Given** historic JSON data from 2022, 2023, or 2024, **When** structure validation runs, **Then** the JSON is verified to contain required top-level fields (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type) matching the expected data model
2. **Given** historic JSON data contains nested structures (meetingInfo, agendaItems), **When** structure validation runs, **Then** nested field structures are verified to match expected patterns (meetingInfo.date, meetingInfo.host, agendaItems[].actionItems, etc.)
3. **Given** historic JSON data contains optional fields that may be missing or null, **When** structure validation runs, **Then** missing optional fields are accepted without causing validation failure
4. **Given** historic JSON data contains structural variations or additional fields not in the base model, **When** structure validation runs, **Then** additional fields are accepted (schema is flexible), but core required fields must be present
5. **Given** historic JSON data fails structure validation, **When** the ingestion script processes multiple sources, **Then** the failed source is skipped with detailed logging, and processing continues for valid sources

---

### User Story 3 - Multi-Source Idempotent Processing (Priority: P2)

A data engineer needs to run historic data ingestion multiple times without creating duplicate records or corrupting existing data, ensuring idempotent behavior across multiple JSON sources.

**Why this priority**: Idempotent processing enables safe re-runs of ingestion scripts, supports incremental updates, and prevents data corruption during troubleshooting or recovery scenarios.

**Independent Test**: Can be fully tested by running the ingestion script multiple times against the same historic JSON sources and verifying that no duplicate records are created, existing records are updated appropriately, and data integrity is maintained. The ingestion provides safe, repeatable data loading.

**Acceptance Scenarios**:

1. **Given** historic data has already been ingested from multiple sources, **When** the ingestion script runs again with the same sources, **Then** no duplicate records are created, and existing records are updated with latest data (UPSERT behavior)
2. **Given** historic data ingestion is run multiple times, **When** records are processed, **Then** workgroup records are updated if they exist, or created if they don't, maintaining referential integrity
3. **Given** historic data ingestion is run multiple times, **When** meeting records are processed, **Then** meetings are updated if they exist (based on unique identifier), or created if they don't, with all nested entities (agenda items, action items, etc.) processed atomically
4. **Given** historic data ingestion encounters conflicts during UPSERT operations, **When** records are processed, **Then** conflicts are logged with sufficient detail (record ID, conflict type, timestamp, source URL) and last-write-wins behavior is applied

---

### Edge Cases

- What happens when one historic JSON URL is unreachable or returns a non-200 status code while others are accessible? → System should continue processing accessible sources and log detailed error for failed source (partial success is acceptable)
- How does the system handle historic JSON files with different structures than expected (e.g., missing required fields)? → Source is skipped with detailed validation error logging, processing continues for valid sources
- What happens when the same meeting record exists in multiple historic year files with different data? → Last-write-wins based on ingestion order, with most recent ingestion taking precedence
- How does the system handle historic JSON files that are extremely large (e.g., 2024 has 552 records)? → System processes files sequentially, handling large datasets within reasonable time limits (e.g., under 10 minutes for all historic sources combined)
- What happens when database connection fails mid-ingestion of historic sources? → System should fail with clear error message; previously committed records from successfully processed sources remain in database
- How does the system handle historic JSON records with workgroup_ids that don't match UUID format? → Record is skipped with detailed validation error logging, processing continues for valid records
- What happens when historic JSON contains dates in unexpected formats or invalid dates? → Invalid date records are skipped with detailed logging, valid records continue processing
- How does the system handle historic JSON sources processed in different orders (e.g., 2022, then 2024, then 2023)? → Order should not affect final data state due to UPSERT behavior, but processing order may affect which version of overlapping records is final
- What happens when historic JSON sources contain workgroups or meetings that overlap with existing 2025 data? → UPSERT behavior applies - existing records are updated with historic data, maintaining single source of truth per unique identifier

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support ingestion from multiple JSON source URLs (2022, 2023, 2024 historic data)
- **FR-002**: System MUST validate JSON structure compatibility with existing data model before processing any records from historic sources
- **FR-003**: System MUST verify that historic JSON contains required top-level fields (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type) matching expected structure
- **FR-004**: System MUST process multiple JSON sources sequentially by default, maintaining transaction integrity and clear error attribution
- **FR-005**: System MUST continue processing remaining valid sources if one historic JSON source fails to download or validate
- **FR-006**: System MUST log detailed error information for failed JSON sources (source URL, error type, error message, timestamp)
- **FR-007**: System MUST apply UPSERT (INSERT ON CONFLICT DO UPDATE) behavior for historic data, updating existing records with last-write-wins strategy
- **FR-008**: System MUST prevent duplicate record creation when processing historic data multiple times
- **FR-009**: System MUST handle overlapping workgroups and meetings across historic sources and existing data without creating duplicates
- **FR-010**: System MUST process all unique workgroups from historic sources first (create if not exists, update if exists) before processing any meetings
- **FR-011**: System MUST link historic meetings to workgroups using workgroup_id foreign key, ensuring workgroups exist before meetings are processed
- **FR-012**: System MUST process historic agenda items and their nested collections (action items, decision items, discussion points) atomically per meeting
- **FR-013**: System MUST preserve original JSON structure from historic sources in raw_json columns for data provenance
- **FR-014**: System MUST handle missing or null optional fields in historic JSON data without causing errors
- **FR-015**: System MUST accept additional fields in historic JSON that are not in the base data model (schema flexibility)
- **FR-016**: System MUST validate data types (e.g., dates, UUIDs) in historic JSON before insertion
- **FR-017**: System MUST skip invalid historic records (malformed structure, invalid UUIDs, invalid dates) with detailed logging and continue processing valid records
- **FR-018**: System MUST process historic data within reasonable time limits (e.g., all historic sources within 10 minutes for typical dataset sizes)
- **FR-019**: System MUST maintain referential integrity when processing historic data (workgroups must exist before meetings, meetings must exist before agenda items)

### Key Entities *(include if feature involves data)*

- **Historic Meeting Summary**: Represents a meeting summary record from years 2022, 2023, or 2024. Key attributes: same as base meeting summary (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type). Relationships: same as base model. Compatibility: Structure matches existing data model, enabling unified processing.
- **Historic Workgroup**: Represents a workgroup from historic years. Key attributes: workgroup_id (UUID), name. Relationships: one-to-many with historic meetings. Compatibility: Same structure as current workgroups, enabling UPSERT operations.
- **Historic Meeting**: Represents a meeting event from historic years. Key attributes: same as base meeting model. Relationships: belongs to one workgroup, has many agenda items. Compatibility: Same structure as current meetings, enabling unified schema handling.
- **Historic Agenda Items**: Represents agenda items from historic meetings. Key attributes: same as base model. Relationships: belongs to one meeting, has nested collections. Compatibility: Same structure as current agenda items, enabling consistent processing.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully ingests 100% of valid JSON records from all historic sources (2022, 2023, 2024) without data loss
- **SC-002**: System processes all historic meeting summary records (approximately 555 total: 552 from 2024, 2 from 2023, 1 from 2022) and inserts them into the database within 10 minutes
- **SC-003**: System validates JSON structure compatibility for 100% of historic sources before processing any records
- **SC-004**: System handles missing or null optional fields in 100% of historic records without failing or corrupting data
- **SC-005**: System can be run multiple times (idempotent) against historic sources without creating duplicate records or data corruption
- **SC-006**: System logs all conflicts and validation errors with sufficient detail (record ID, source URL, error type, timestamp) for 100% of error cases
- **SC-007**: System continues processing remaining valid historic sources when one source fails, achieving partial success rather than complete failure
- **SC-008**: System applies UPSERT behavior correctly, updating existing records from historic sources without creating duplicates
- **SC-009**: System maintains referential integrity when processing historic data (all workgroups exist before meetings, all meetings exist before agenda items)
- **SC-010**: System preserves original JSON data from historic sources in raw_json columns for 100% of records, enabling full data provenance
- **SC-011**: System validates JSON structure and rejects incompatible historic data before attempting database insertion, preventing partial data corruption
- **SC-012**: Historic data ingestion integrates seamlessly with existing 2025 data ingestion, using the same schema and processing logic

## Assumptions

- Historic JSON sources (2022, 2023, 2024) follow the same structure as 2025 data, with potential minor variations in optional fields
- Historic JSON structure is compatible with existing data model (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type fields)
- Network access to all historic JSON source URLs is available
- Database schema from feature 001 is already deployed and supports historic data ingestion
- Workgroup IDs in historic JSON are valid UUIDs (or can be validated/skipped if invalid)
- Historic data may contain overlapping records with existing 2025 data, requiring UPSERT behavior
- Processing order of historic sources may affect which version of overlapping records is final (last-write-wins)
- Historic JSON sources may have different record counts and file sizes (2024: 552 records, 2023: 2 records, 2022: 1 record)
