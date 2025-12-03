# Meeting Summaries Data Ingestion Pipeline

A Python-based data ingestion pipeline that downloads meeting summary JSON data from multiple GitHub URLs, validates structure compatibility, and stores it in a normalized PostgreSQL/Supabase schema.

## Features

- **Multi-Source JSON Data Ingestion**: Downloads and processes meeting summaries from multiple sources (2022-2025)
  - Supports historic data from 2022, 2023, 2024, and current data from 2025
  - Processes multiple JSON sources sequentially with transaction integrity
  - Continues processing remaining sources if one source fails
- **Structure Validation**: Validates JSON compatibility before ingestion
  - Validates structure compatibility for all historic sources before processing any records
  - Handles missing optional fields and accepts additional fields for schema flexibility
- **Normalized Storage**: Stores data in PostgreSQL with normalized relational tables and JSONB columns
- **Idempotent Processing**: UPSERT operations prevent duplicates on re-runs
  - Last-write-wins strategy for overlapping records across sources
  - Safe to run multiple times without data corruption
- **Structured Logging**: JSON-formatted logs with detailed error information
  - Includes source URL, error type, error message, and timestamp for all errors
- **Containerized Deployment**: Docker support for Supabase deployment

## Prerequisites

- Python 3.8+
- PostgreSQL 12+ (or Supabase)
- pip

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd data-ingestion
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. Create database schema:
```bash
psql -U postgres -d meeting_summaries -f scripts/setup_db.sql
```

## Usage

### Basic Usage

```bash
# Ingest from default URLs (includes 2022, 2023, 2024, 2025 historic and current data)
python -m src.cli.ingest

# Specify custom URLs (processes multiple sources sequentially)
python -m src.cli.ingest \
  https://raw.githubusercontent.com/.../2025/meeting-summaries-array.json \
  https://raw.githubusercontent.com/.../2024/meeting-summaries-array.json \
  https://raw.githubusercontent.com/.../2023/meeting-summaries-array.json \
  https://raw.githubusercontent.com/.../2022/meeting-summaries-array.json

# Dry run (validate without inserting)
python -m src.cli.ingest --dry-run

# Verbose logging
python -m src.cli.ingest --verbose
```

### Historic Data Support

The pipeline supports ingestion of historic meeting summary data from multiple years:

- **Default Sources**: The CLI includes default URLs for 2022, 2023, 2024, and 2025 data
- **Sequential Processing**: Sources are processed sequentially to maintain transaction integrity
- **Error Handling**: If one source fails to download or validate, processing continues with remaining sources
- **Structure Validation**: Each historic source is validated for structure compatibility before processing
- **Idempotent**: Running ingestion multiple times updates existing records without creating duplicates
- **Referential Integrity**: All workgroups are processed first, then meetings, ensuring proper relationships

### Command Options

- `--database-url`, `-d`: PostgreSQL connection string (default: `$DATABASE_URL`)
- `--db-password`, `-p`: Database password (if not in URL)
- `--dry-run`: Validate and parse data without inserting to database
- `--verbose`, `-v`: Enable verbose logging
- `--log-format`: Log format (`json` or `text`, default: `json`)

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (required)
- `DB_PASSWORD`: Database password (if not in URL)
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, default: `INFO`)
- `LOG_FORMAT`: Log format (`json` or `text`, default: `json`)

## Project Structure

```
src/
├── models/          # Database models and Pydantic schemas
├── services/        # Business logic and data processing
├── db/              # Database connection and utilities
├── cli/             # Command-line interface
└── lib/             # Shared utilities (logging, validation)

tests/
├── contract/        # Contract tests
├── integration/     # Integration tests
└── unit/            # Unit tests

scripts/
├── setup_db.sql     # Database schema DDL
└── docker/          # Docker configuration
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Deployment

### Production Deployment

For production deployment to Supabase or other containerized environments:

1. **Build Docker Image**
   ```bash
   docker build -t data-ingestion:latest -f scripts/docker/Dockerfile .
   ```

2. **Configure Environment Variables**
   - Set `DATABASE_URL` with your production database connection string
   - Set `LOG_LEVEL` (default: `INFO`)
   - Set `LOG_FORMAT` (default: `json`)

3. **Run Container**
   ```bash
   docker run --env-file .env data-ingestion:latest
   ```

4. **Verify Deployment**
   - Check logs for successful ingestion
   - Verify record counts in database
   - Test idempotent re-runs

See `PRODUCTION_CHECKLIST.md` for detailed production deployment checklist.

### Local Development

See `specs/001-meeting-summaries-ingestion/quickstart.md` for local development setup instructions.

## Documentation

### Core Documentation
- **Specification**: `specs/001-meeting-summaries-ingestion/spec.md`
- **Implementation Plan**: `specs/001-meeting-summaries-ingestion/plan.md`
- **Data Model**: `specs/001-meeting-summaries-ingestion/data-model.md`
- **Quickstart Guide**: `specs/001-meeting-summaries-ingestion/quickstart.md`

### Operations Documentation
- **Production Checklist**: `PRODUCTION_CHECKLIST.md` - Environment configuration and pre-deployment verification
- **Troubleshooting Guide**: `TROUBLESHOOTING.md` - Common issues and solutions
- **Operations Runbook**: `OPERATIONS_RUNBOOK.md` - Step-by-step operational procedures
- **Changelog**: `CHANGELOG.md` - Version history and release notes

## License

[Add license information]
