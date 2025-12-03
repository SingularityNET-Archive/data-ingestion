---
description: "Task list for Meeting Summaries Data Ingestion Pipeline implementation"
---

# Tasks: Meeting Summaries Data Ingestion Pipeline

**Input**: Design documents from `/specs/001-meeting-summaries-ingestion/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - only include them if explicitly requested in the feature specification or if user requests TDD approach.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (src/models/, src/services/, src/db/, src/cli/, src/lib/, tests/)
- [X] T002 Initialize Python project with dependencies (requirements.txt with fastapi, asyncpg, httpx, pydantic, python-dotenv, click, pytest, pytest-asyncio)
- [X] T003 [P] Configure linting and formatting tools (setup black, flake8/mypy, or ruff in pyproject.toml or setup.cfg)
- [X] T004 [P] Create .gitignore file excluding venv/, __pycache__/, .env, *.pyc, .pytest_cache/
- [X] T005 [P] Create README.md with project overview and setup instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Setup database connection utilities in src/db/connection.py (asyncpg connection pool, environment variable support)
- [X] T007 Create structured JSON logging utility in src/lib/logger.py (stdout/stderr, JSON format, log levels)
- [X] T008 Create validation utilities in src/lib/validators.py (UUID validation, date parsing, circular reference detection)
- [X] T009 Setup environment configuration management (python-dotenv support for DATABASE_URL, DB_PASSWORD, LOG_LEVEL, LOG_FORMAT)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Database Schema Creation (Priority: P1) 🎯 MVP

**Goal**: Create a normalized database schema that can store meeting summary data from JSON sources while maintaining flexibility for future schema changes and preserving original data for provenance.

**Independent Test**: Execute SQL DDL statements against a PostgreSQL database and verify that all tables are created with correct relationships, constraints, and indexes. The schema delivers a structured data model that supports both relational queries and flexible JSON operations.

### Implementation for User Story 1

- [X] T010 [US1] Create SQL schema DDL script in scripts/setup_db.sql with workgroups table (UUID primary key, name, raw_json JSONB, timestamps, GIN index)
- [X] T011 [US1] Add meetings table to SQL schema script (UUID primary key, workgroup_id foreign key, normalized fields, JSONB columns, indexes)
- [X] T012 [US1] Add agenda_items table to SQL schema script (UUID primary key, meeting_id foreign key, status, order_index, raw_json JSONB, indexes)
- [X] T013 [US1] Add action_items table to SQL schema script (UUID primary key, agenda_item_id foreign key, text, assignee, due_date, status, raw_json JSONB, indexes)
- [X] T014 [US1] Add decision_items table to SQL schema script (UUID primary key, agenda_item_id foreign key, decision_text, rationale, effect_scope, raw_json JSONB, indexes)
- [X] T015 [US1] Add discussion_points table to SQL schema script (UUID primary key, agenda_item_id foreign key, point_text, raw_json JSONB, indexes)
- [X] T016 [US1] Add UPSERT functions to SQL schema script (upsert_workgroup, upsert_meeting, upsert_agenda_item, upsert_action_item, upsert_decision_item, upsert_discussion_point)
- [X] T017 [US1] Create database migration utility in src/db/migrations.py to execute SQL schema script
- [X] T018 [US1] Add SQL comments explaining table purposes and column meanings to schema script

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - database schema can be created and verified

---

## Phase 4: User Story 2 - JSON Data Ingestion (Priority: P1) 🎯 MVP

**Goal**: Download meeting summary JSON data from multiple remote URLs (2025 current data and historic data from 2022, 2023, 2024), validate its structure compatibility with the data model, and insert it into the database schema with normalized fields extracted and nested objects stored in JSONB columns.

**Independent Test**: Run the ingestion script against a test database with sample JSON data from multiple sources and verify that all records are inserted correctly with normalized fields populated and original JSON preserved. The ingestion delivers structured, queryable data from unstructured JSON sources across multiple years.

### Implementation for User Story 2

- [X] T019 [P] [US2] Create JSON downloader service in src/services/json_downloader.py (httpx async client, download from URLs, error handling)
- [X] T020 [US2] Create Pydantic models in src/models/meeting_summary.py (MeetingInfo, ActionItem, DecisionItem, DiscussionPoint, AgendaItem, MeetingSummary, MeetingSummaryArray)
- [X] T021 [US2] Create JSON validator service in src/services/json_validator.py (structure compatibility check, record validation using Pydantic models)
- [X] T022 [US2] Create database model classes in src/models/workgroup.py (Workgroup model with fields matching schema)
- [X] T023 [P] [US2] Create database model classes in src/models/meeting.py (Meeting model with fields matching schema)
- [X] T024 [P] [US2] Create database model classes in src/models/agenda_item.py (AgendaItem model with fields matching schema)
- [X] T025 [P] [US2] Create database model classes in src/models/action_item.py (ActionItem model with fields matching schema)
- [X] T026 [P] [US2] Create database model classes in src/models/decision_item.py (DecisionItem model with fields matching schema)
- [X] T027 [P] [US2] Create database model classes in src/models/discussion_point.py (DiscussionPoint model with fields matching schema)
- [X] T028 [US2] Create schema manager service in src/services/schema_manager.py (workgroup pre-processing: extract unique workgroups, UPSERT all workgroups first)
- [X] T029 [US2] Create ingestion service in src/services/ingestion_service.py (per-meeting atomic transactions, process meetings with nested entities, UPSERT logic)
- [X] T030 [US2] Implement workgroup extraction and UPSERT logic in ingestion_service.py (collect unique workgroups from all sources, UPSERT before meetings)
- [X] T031 [US2] Implement meeting processing with nested entities in ingestion_service.py (per-meeting transaction: meeting + agenda items + action items + decision items + discussion points)
- [X] T032 [US2] Implement field extraction and normalization in ingestion_service.py (extract normalized fields to relational columns, store nested objects in JSONB)
- [X] T033 [US2] Implement error handling in ingestion_service.py (skip invalid records with detailed logging, continue processing valid records)
- [X] T034 [US2] Create CLI command in src/cli/ingest.py (Click command, URL arguments, options for database-url, dry-run, verbose, log-format)

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently - JSON data can be downloaded, validated, and ingested into database

---

## Phase 5: User Story 3 - JSON Structure Compatibility Validation (Priority: P1) 🎯 MVP

**Goal**: Verify that JSON data from different years (2022, 2023, 2024, 2025) is compatible with the existing data model before attempting ingestion, preventing data corruption and ensuring consistent schema handling.

**Independent Test**: Run validation checks against sample JSON from each year and verify that structure matches expected data model (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type fields). The validation ensures data compatibility and prevents schema mismatches.

### Implementation for User Story 3

- [X] T035 [US3] Enhance JSON validator service in src/services/json_validator.py with structure compatibility validation (check required top-level fields: workgroup, workgroup_id, meetingInfo, agendaItems, tags, type)
- [X] T036 [US3] Add nested structure validation in json_validator.py (validate meetingInfo.date, agendaItems array structure, nested field patterns)
- [X] T037 [US3] Add optional field handling in json_validator.py (accept missing optional fields, accept additional fields for schema flexibility)
- [X] T038 [US3] Integrate structure validation into ingestion service in src/services/ingestion_service.py (validate each source before processing any records, skip incompatible sources with logging)
- [X] T039 [US3] Add validation error logging in ingestion_service.py (log source URL, validation errors, continue processing valid sources)

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently - JSON structure compatibility can be validated before ingestion

---

## Phase 6: User Story 4 - Idempotent Data Processing (Priority: P2)

**Goal**: Run the ingestion script multiple times without creating duplicate records or losing data integrity, with conflicts logged for review.

**Independent Test**: Run the ingestion script twice with the same data source and verify that no duplicate records are created, conflicts are logged appropriately, and data integrity is maintained. The idempotent behavior delivers reliable, repeatable data processing.

### Implementation for User Story 4

- [X] T040 [US4] Verify UPSERT implementation in ingestion_service.py uses INSERT ON CONFLICT DO UPDATE with last-write-wins strategy
- [X] T041 [US4] Add conflict logging in ingestion_service.py (log record identifier, conflict type, timestamp, source URL when conflicts occur)
- [X] T042 [US4] Ensure updated_at timestamp is set correctly on UPSERT operations in all model UPSERT functions
- [X] T043 [US4] Test idempotent behavior by running ingestion twice and verifying no duplicates and proper updates

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently - ingestion can be run multiple times without duplicates

---

## Phase 7: User Story 5 - Local Development and Testing (Priority: P2)

**Goal**: Run the ingestion pipeline locally for development, testing, and debugging before deploying to production.

**Independent Test**: Follow the provided local setup instructions and successfully run the ingestion script against a local database. The local setup delivers a complete development environment for testing and debugging.

### Implementation for User Story 5

- [X] T044 [US5] Create local setup instructions in quickstart.md (virtual environment, dependencies, database setup, environment variables)
- [X] T045 [US5] Add database setup script in scripts/setup_db.sh (create database, run migrations, verify schema)
- [X] T046 [US5] Create example .env.example file with DATABASE_URL, DB_PASSWORD, LOG_LEVEL, LOG_FORMAT placeholders
- [X] T047 [US5] Add CLI help documentation and usage examples in src/cli/ingest.py docstrings
- [X] T048 [US5] Test local execution with sample data and verify all components work together

**Checkpoint**: At this point, User Story 5 should be fully functional and testable independently - developers can set up and run ingestion locally

---

## Phase 8: User Story 6 - Containerized Deployment to Supabase (Priority: P3)

**Goal**: Deploy the ingestion pipeline as a containerized job that can run on Supabase infrastructure, either on-demand or on a schedule.

**Independent Test**: Build a container image, deploy it to Supabase, and verify that the ingestion job executes successfully in the containerized environment. The deployment delivers a production-ready, maintainable data ingestion solution.

### Implementation for User Story 6

- [X] T049 [US6] Create Dockerfile in scripts/docker/Dockerfile (Python 3.9-slim base, multi-stage build, install dependencies, copy application code)
- [X] T050 [US6] Create docker-compose.yml in scripts/docker/docker-compose.yml for local container testing
- [X] T051 [US6] Create .dockerignore file to exclude unnecessary files from Docker build
- [X] T052 [US6] Add container deployment instructions to quickstart.md (build image, push to registry, deploy to Supabase, configure environment variables)
- [X] T053 [US6] Test container build and local execution with docker-compose
- [X] T054 [US6] Verify containerized execution connects to Supabase database and processes data correctly

**Checkpoint**: At this point, User Story 6 should be fully functional and testable independently - containerized deployment is ready for Supabase

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T055 [P] Add comprehensive error handling for network errors (connection timeout, HTTP errors, invalid URLs) in json_downloader.py
- [X] T056 [P] Add comprehensive error handling for database errors (connection failure, transaction failure, constraint violations) in ingestion_service.py
- [X] T057 [P] Add circular reference detection in src/lib/validators.py (max depth check, skip records with circular references, log warnings)
- [X] T058 [P] Add Unicode and emoji support verification (UTF-8 encoding, PostgreSQL TEXT/JSONB Unicode support) in ingestion_service.py
- [X] T059 [P] Add empty array and null value handling (store empty arrays as [], NULL as NULL) in ingestion_service.py
- [X] T060 [P] Add progress logging for large datasets (log records processed, total records, source URL) in ingestion_service.py
- [X] T061 [P] Update README.md with complete project documentation (setup, usage, deployment, troubleshooting)
- [X] T062 [P] Run quickstart.md validation (test all instructions end-to-end)
- [X] T063 [P] Code cleanup and refactoring (ensure consistent error handling, logging patterns, code style)
- [X] T064 [P] Performance optimization (connection pooling, batch processing if needed, verify 10-minute goal for 677 records)

---

## Phase 10: Historic Data Ingestion Verification & Enhancement

**Purpose**: Ensure all historic data requirements from spec 002 are fully implemented and verified

**Input**: Feature specification from `/specs/002-include-historic-data/spec.md`

- [X] T065 [US2-HIST] Verify historic data URLs (2022, 2023, 2024) are included in DEFAULT_URLS in src/cli/ingest.py
- [X] T066 [US2-HIST] Verify sequential processing of multiple JSON sources maintains transaction integrity in src/cli/ingest.py
- [X] T067 [US2-HIST] Verify structure validation occurs before processing any records from historic sources in src/services/json_validator.py
- [X] T068 [US2-HIST] Verify system continues processing remaining valid sources when one historic source fails in src/cli/ingest.py
- [X] T069 [US2-HIST] Verify detailed error logging for failed JSON sources includes source URL, error type, error message, timestamp in src/cli/ingest.py
- [X] T070 [US2-HIST] Verify UPSERT behavior applies correctly for historic data with last-write-wins strategy in src/services/ingestion_service.py
- [X] T071 [US2-HIST] Verify all unique workgroups from historic sources are processed first before meetings in src/services/ingestion_service.py
- [X] T072 [US2-HIST] Verify historic data processing maintains referential integrity (workgroups exist before meetings, meetings exist before agenda items) in src/services/ingestion_service.py
- [X] T073 [US2-HIST] Verify historic JSON structure validation checks required top-level fields (workgroup, workgroup_id, meetingInfo, agendaItems, tags, type) in src/services/json_validator.py
- [X] T074 [US2-HIST] Verify missing or null optional fields in historic JSON are handled without errors in src/services/json_validator.py
- [X] T075 [US2-HIST] Verify additional fields in historic JSON not in base model are accepted (schema flexibility) in src/services/json_validator.py
- [X] T076 [US2-HIST] Verify idempotent behavior works correctly when running historic data ingestion multiple times in src/services/ingestion_service.py
- [X] T077 [US2-HIST] Test historic data ingestion end-to-end with all historic sources (2022, 2023, 2024) and verify all records are processed correctly
- [X] T078 [US2-HIST] Update documentation to explicitly mention historic data support and multi-source processing in README.md

**Checkpoint**: At this point, Phase 10 should be complete - historic data ingestion is fully verified and all spec 002 requirements are met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 (needs database schema)
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Can be integrated with US2 (validation before ingestion)
- **User Story 4 (P2)**: Can start after US2 is complete - Enhances US2 with idempotency
- **User Story 5 (P2)**: Can start after US2 is complete - Provides local development support
- **User Story 6 (P3)**: Can start after US2 is complete - Provides containerized deployment

### Within Each User Story

- Models before services
- Services before CLI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1, 2, and 3 can start (US2 depends on US1, US3 can integrate with US2)
- All database model tasks (T022-T027) marked [P] can run in parallel
- All error handling tasks (T055-T060) marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members after dependencies are met

---

## Parallel Example: User Story 2

```bash
# Launch all database models for User Story 2 together:
Task: "Create database model classes in src/models/meeting.py"
Task: "Create database model classes in src/models/agenda_item.py"
Task: "Create database model classes in src/models/action_item.py"
Task: "Create database model classes in src/models/decision_item.py"
Task: "Create database model classes in src/models/discussion_point.py"

# Launch all error handling improvements together:
Task: "Add comprehensive error handling for network errors in json_downloader.py"
Task: "Add comprehensive error handling for database errors in ingestion_service.py"
Task: "Add circular reference detection in src/lib/validators.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Database Schema)
4. Complete Phase 4: User Story 2 (JSON Data Ingestion)
5. Complete Phase 5: User Story 3 (Structure Validation)
6. **STOP and VALIDATE**: Test all three stories independently and together
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Schema ready
3. Add User Story 2 → Test independently → Basic ingestion works
4. Add User Story 3 → Test independently → Validation prevents errors
5. Add User Story 4 → Test independently → Idempotent re-runs work
6. Add User Story 5 → Test independently → Local development ready
7. Add User Story 6 → Test independently → Containerized deployment ready
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Schema)
   - Developer B: Prepares for User Story 2 (models, downloader)
3. Once User Story 1 is complete:
   - Developer A: User Story 2 (Ingestion service)
   - Developer B: User Story 3 (Validation enhancements)
   - Developer C: User Story 4 (Idempotency verification)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify schema creation before implementing ingestion
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests are OPTIONAL - only include if explicitly requested
- All tasks include exact file paths for clarity

---

## Task Summary

- **Total Tasks**: 78
- **Setup Tasks**: 5 (Phase 1)
- **Foundational Tasks**: 4 (Phase 2)
- **User Story 1 Tasks**: 9 (Phase 3)
- **User Story 2 Tasks**: 16 (Phase 4)
- **User Story 3 Tasks**: 5 (Phase 5)
- **User Story 4 Tasks**: 4 (Phase 6)
- **User Story 5 Tasks**: 5 (Phase 7)
- **User Story 6 Tasks**: 6 (Phase 8)
- **Polish Tasks**: 10 (Phase 9)
- **Historic Data Tasks**: 14 (Phase 10)

- **Parallel Opportunities Identified**: 
  - Setup tasks (T003-T005)
  - Database models (T023-T027)
  - Error handling improvements (T055-T060)
  - Multiple user stories can proceed in parallel after dependencies met

- **Independent Test Criteria**:
  - **US1**: Execute SQL DDL, verify tables created with relationships and indexes
  - **US2**: Run ingestion script, verify records inserted with normalized fields and JSON preserved
  - **US3**: Run validation checks, verify structure compatibility before ingestion
  - **US4**: Run ingestion twice, verify no duplicates and proper updates
  - **US5**: Follow setup instructions, run ingestion locally successfully
  - **US6**: Build container, deploy to Supabase, verify execution

- **Suggested MVP Scope**: User Stories 1, 2, 3 (P1 priorities) - Database schema, JSON ingestion, and structure validation
