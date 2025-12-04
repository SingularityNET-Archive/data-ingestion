# Changelog

All notable changes to the Meeting Summaries Data Ingestion Pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-03

### Added

#### Core Features
- **Multi-Source JSON Data Ingestion**: Download and process meeting summaries from multiple GitHub URLs (2022-2025)
- **Structure Validation**: Validate JSON compatibility before ingestion to prevent data corruption
- **Normalized Database Schema**: PostgreSQL schema with normalized relational tables and JSONB columns
- **Idempotent Processing**: UPSERT operations prevent duplicates on re-runs with last-write-wins strategy
- **Structured Logging**: JSON-formatted logs with detailed error information and progress tracking

#### Database Schema
- Tables: `workgroups`, `meetings`, `agenda_items`, `action_items`, `decision_items`, `discussion_points`
- UUID primary keys for all tables
- Foreign key relationships maintaining referential integrity
- GIN indexes on JSONB columns for efficient JSON queries
- `raw_json` JSONB columns preserving original data for provenance

#### Services
- **JSON Downloader**: Async HTTP client for downloading JSON from remote URLs
- **JSON Validator**: Structure compatibility validation and record validation using Pydantic models
- **Schema Manager**: Workgroup pre-processing and unique extraction
- **Ingestion Service**: Per-meeting atomic transactions with nested entity processing

#### CLI Interface
- Command-line interface with Click
- Support for multiple JSON source URLs
- Dry-run mode for validation without insertion
- Verbose logging option
- Configurable log format (JSON or text)

#### Testing
- Comprehensive unit tests for all components
- Integration tests for full pipeline
- Contract tests for JSON structure validation
- End-to-end tests with test database
- Performance tests verifying 10-minute goal
- Error handling tests for failure scenarios

#### Deployment
- GitHub Actions workflow for automated scheduled execution
- Zero-infrastructure deployment (no containers or servers needed)
- Manual workflow trigger support
- Production deployment documentation

#### Documentation
- Complete specification and implementation plan
- Data model documentation
- Quickstart guide for local development
- Production deployment checklist
- Troubleshooting guide
- Operations runbook

### Technical Details

#### Dependencies
- Python 3.8+
- FastAPI framework
- asyncpg for async PostgreSQL operations
- httpx for async HTTP requests
- Pydantic V2 for data validation
- Click for CLI interface
- pytest for testing

#### Features
- UTF-8 encoding support for Unicode and emoji
- Circular reference detection
- Empty array and null value handling
- Per-meeting atomic transactions
- Sequential source processing with error recovery
- Detailed error logging with source attribution

### Changed

- Migrated from Pydantic V1 to V2:
  - Replaced `@validator` with `@field_validator`
  - Replaced `class Config` with `model_config = ConfigDict`
  - Replaced `.dict()` with `.model_dump()`
  - Replaced `.json()` with `.model_dump_json()`

### Fixed

- Pydantic V2 deprecation warnings
- Code formatting issues (black)
- Linting issues (unused imports, trailing whitespace)
- Import organization

### Security

- Environment variable support for sensitive credentials
- Secure defaults for configuration
- Documentation warnings about credential management

### Performance

- Connection pooling for database operations
- Efficient JSONB storage and querying
- Optimized database indexes
- Target: Process 677 records within 10 minutes

## [Unreleased]

### Changed
- **Repository Organization**: Comprehensive repository reorganization for improved clarity and maintainability
  - **Documentation Structure**: Consolidated all documentation into `docs/` directory with logical subdirectories
    - Operations guides moved to `docs/operations/` (runbook, production checklist, troubleshooting, duplicate diagnosis)
    - Deployment guides moved to `docs/deployment/` (Supabase setup, quick start, deployment options)
    - Historical files archived in `docs/archive/` (data structure analysis)
  - **Script Organization**: Moved all utility scripts from root to `scripts/` directory
    - `check_duplicates.py` → `scripts/check_duplicates.py`
    - `find_missing_meetings.py` → `scripts/find_missing_meetings.py`
    - `run_migration.py` → `scripts/run_migration.py`
    - `verify_schema.py` → `scripts/verify_schema.py`
  - **File Naming**: Converted documentation files to kebab-case naming convention
    - `OPERATIONS_RUNBOOK.md` → `docs/operations/runbook.md`
    - `PRODUCTION_CHECKLIST.md` → `docs/operations/production-checklist.md`
    - `TROUBLESHOOTING.md` → `docs/operations/troubleshooting.md`
    - `DUPLICATE_DIAGNOSIS.md` → `docs/operations/duplicate-diagnosis.md`
    - `SUPABASE_SETUP_GUIDE.md` → `docs/deployment/supabase-setup.md`
    - `SUPABASE_QUICK_START.md` → `docs/deployment/supabase-quickstart.md`
    - `SUPABASE_DEPLOYMENT_OPTIONS.md` → `docs/deployment/deployment-options.md`
  - **Documentation Updates**: Updated all cross-references in README.md and documentation files to reflect new paths
  - **Documentation Index**: Created `docs/README.md` as comprehensive documentation index with navigation

### Added
- **Documentation Index**: Created `docs/README.md` with organized navigation and technical term definitions
- **Archive Directory**: Created `docs/archive/` for historical and analysis files

### Removed
- **Log Files**: Removed log files from git tracking (already gitignored, now explicitly removed)
  - `ingestion.log`, `local_ingestion_flexible.log`, `local_ingestion.log` (gitignored, not tracked)

### Changed (continued)
- **Deployment Method**: Migrated from Docker containerization to GitHub Actions workflow
  - Removed Docker-specific deployment instructions
  - Added GitHub Actions workflow (`.github/workflows/ingest-meetings.yml`)
  - Updated all documentation to reflect GitHub Actions as primary deployment method
  - Simplified deployment process (no container registry or orchestration needed)

### Planned
- Parallel source processing option
- Incremental ingestion support
- Data export functionality
- API endpoints for querying ingested data

