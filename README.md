# Meeting Summaries Data Ingestion Pipeline

A Python-based data ingestion pipeline that downloads meeting summary JSON data from multiple GitHub URLs, validates structure compatibility, and stores it in a normalized PostgreSQL/Supabase schema.

## Features

- **JSON Data Ingestion**: Downloads and processes meeting summaries from multiple sources (2022-2025)
- **Structure Validation**: Validates JSON compatibility before ingestion
- **Normalized Storage**: Stores data in PostgreSQL with normalized relational tables and JSONB columns
- **Idempotent Processing**: UPSERT operations prevent duplicates on re-runs
- **Structured Logging**: JSON-formatted logs for observability
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
# Ingest from default URLs
python -m src.cli.ingest

# Specify custom URLs
python -m src.cli.ingest \
  https://raw.githubusercontent.com/.../2025/meeting-summaries-array.json \
  https://raw.githubusercontent.com/.../2024/meeting-summaries-array.json

# Dry run (validate without inserting)
python -m src.cli.ingest --dry-run

# Verbose logging
python -m src.cli.ingest --verbose
```

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

See `specs/001-meeting-summaries-ingestion/quickstart.md` for containerized deployment instructions.

## Documentation

- **Specification**: `specs/001-meeting-summaries-ingestion/spec.md`
- **Implementation Plan**: `specs/001-meeting-summaries-ingestion/plan.md`
- **Data Model**: `specs/001-meeting-summaries-ingestion/data-model.md`
- **Quickstart Guide**: `specs/001-meeting-summaries-ingestion/quickstart.md`

## License

[Add license information]
