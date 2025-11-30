# Implementation Plan: Meeting Summaries Data Ingestion Pipeline

**Branch**: `001-meeting-summaries-ingestion` | **Date**: 2025-11-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-meeting-summaries-ingestion/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a Python FastAPI-based data ingestion pipeline that downloads meeting summary JSON data from multiple GitHub URLs (2022-2025), validates structure compatibility, and stores it in a normalized PostgreSQL/Supabase schema. The system will extract normalized fields into relational tables while preserving original JSON in JSONB columns for provenance. Implementation includes idempotent UPSERT processing, per-meeting atomic transactions, structured logging, and containerized deployment support.

## Technical Context

**Language/Version**: Python 3.8+  
**Primary Dependencies**: FastAPI, asyncpg (or psycopg2), httpx (or requests), pydantic (for validation), python-dotenv  
**Storage**: PostgreSQL/Supabase with JSONB support  
**Testing**: pytest, pytest-asyncio (if using asyncpg)  
**Target Platform**: Linux server (containerized for Supabase deployment)  
**Project Type**: single (data ingestion pipeline/CLI tool)  
**Performance Goals**: Process all sources (677 records across 4 years) within 10 minutes  
**Constraints**: Per-record transactions for atomicity, structured JSON logging to stdout/stderr, UTF-8 encoding for Unicode/emoji support, max nesting depth check for circular references  
**Scale/Scope**: ~677 meeting records (122 from 2025, 552 from 2024, 2 from 2023, 1 from 2022) with nested entities (agenda items, action items, decision items, discussion points)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: Constitution file at `.specify/memory/constitution.md` is currently a template with placeholders. No specific constitutional gates are defined at this time. Proceeding with implementation planning based on feature specification requirements.

**Design Principles Applied**:
- Single project structure (data ingestion pipeline)
- Clear separation of concerns (schema, ingestion logic, validation)
- Idempotent operations (UPSERT pattern)
- Structured logging for observability
- Containerized deployment support

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── models/              # Database models and schema definitions
│   ├── __init__.py
│   ├── workgroup.py
│   ├── meeting.py
│   ├── agenda_item.py
│   ├── action_item.py
│   ├── decision_item.py
│   └── discussion_point.py
├── services/            # Business logic and data processing
│   ├── __init__.py
│   ├── json_downloader.py
│   ├── json_validator.py
│   ├── schema_manager.py
│   └── ingestion_service.py
├── db/                  # Database connection and utilities
│   ├── __init__.py
│   ├── connection.py
│   └── migrations.py
├── cli/                 # Command-line interface
│   ├── __init__.py
│   └── ingest.py
└── lib/                 # Shared utilities
    ├── __init__.py
    ├── logger.py
    └── validators.py

tests/
├── contract/            # Contract tests for data validation
├── integration/         # Integration tests for full pipeline
└── unit/                # Unit tests for individual components

scripts/                 # Deployment and utility scripts
├── setup_db.sh
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

**Structure Decision**: Single project structure chosen as this is a data ingestion pipeline/CLI tool rather than a web application. The structure separates concerns into models (data definitions), services (business logic), db (database utilities), cli (entry point), and lib (shared utilities). Tests are organized by type (contract, integration, unit) to support different testing strategies.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
